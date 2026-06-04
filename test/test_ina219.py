"""INA219 register logic tested against a fake SMBus (no hardware needed)."""
import powerguess.ina219 as ina_mod


class FakeSMBus:
    # Register -> raw 16-bit value the chip would return.
    REGS = {
        0x02: 0x2580,  # bus voltage reg: (0x2580 >> 3) * 4mV = 4.8 V
        0x01: 0x000A,  # shunt reg: 10 * 0.01 / 0.1 ohm = 1.0 A
        0x03: 0x0032,  # power reg: 50 * 100uA * 20 = 0.1 W
    }

    def __init__(self, bus):
        self.bus = bus
        self.writes = []

    def write_i2c_block_data(self, addr, reg, data):
        self.writes.append((reg, data))

    def read_i2c_block_data(self, addr, reg, n):
        v = self.REGS.get(reg, 0)
        return [(v >> 8) & 0xFF, v & 0xFF]

    def close(self):
        pass


def test_ina219_read(monkeypatch):
    monkeypatch.setattr(ina_mod, "SMBus", FakeSMBus)
    ina = ina_mod.INA219(bus=1, address=0x40, shunt_ohms=0.1)
    voltage, current, power = ina.read()
    assert round(voltage, 2) == 4.8
    assert round(current, 2) == 1.0
    assert round(power, 2) == 0.1
    # config + calibration registers were written at init
    assert any(reg == 0x00 for reg, _ in ina._bus.writes)
    assert any(reg == 0x05 for reg, _ in ina._bus.writes)
    ina.close()


def test_ina219_requires_smbus(monkeypatch):
    import pytest
    monkeypatch.setattr(ina_mod, "SMBus", None)
    with pytest.raises(ImportError):
        ina_mod.INA219()


def test_ina219_signed_current(monkeypatch):
    monkeypatch.setattr(ina_mod, "SMBus", FakeSMBus)
    ina = ina_mod.INA219()
    # negative shunt reading -> magnitude returned
    assert ina._signed(0xFFFF) == -1
