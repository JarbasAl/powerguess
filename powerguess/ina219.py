"""Optional INA219 I²C power-monitor reader (the ``ina219`` extra).

Many Raspberry Pi / SBC power HATs expose a real bus voltage and shunt current
over I²C through a TI INA219. Reading it gives a *measured* power figure on
exactly the headless devices where the CPU-load estimate is weakest. Needs
``smbus2`` and the chip wired on an I²C bus.

    from powerguess.ina219 import INA219
    ina = INA219(bus=1, address=0x40)
    voltage, current, power = ina.read()
"""

from __future__ import annotations

try:
    from smbus2 import SMBus
except ImportError:  # pragma: no cover - hardware/dep optional
    SMBus = None

# INA219 registers.
_REG_CONFIG = 0x00
_REG_SHUNT = 0x01
_REG_BUS = 0x02
_REG_POWER = 0x03
_REG_CALIBRATION = 0x05


class INA219:
    """Minimal INA219 reader for a 32 V / 2 A range with a 0.1 Ω shunt.

    :param bus: I²C bus number (1 on most Raspberry Pis).
    :param address: I²C address (0x40 default).
    :param shunt_ohms: shunt resistor value.
    """

    def __init__(self, bus: int = 1, address: int = 0x40,
                 shunt_ohms: float = 0.1):
        if SMBus is None:
            raise ImportError("INA219 needs smbus2: pip install powerguess[ina219]")
        self.address = address
        self.shunt_ohms = shunt_ohms
        self._bus = SMBus(bus)
        # 32V range, 320mV gain, 12-bit ADCs, continuous shunt+bus.
        self._write(_REG_CONFIG, 0x399F)
        # Calibration for ~0.1 Ω shunt: current_lsb = 100 µA.
        self._current_lsb = 0.0001
        cal = int(0.04096 / (self._current_lsb * shunt_ohms))
        self._write(_REG_CALIBRATION, cal)

    def _write(self, reg: int, value: int) -> None:
        self._bus.write_i2c_block_data(self.address, reg,
                                       [(value >> 8) & 0xFF, value & 0xFF])

    def _read(self, reg: int) -> int:
        data = self._bus.read_i2c_block_data(self.address, reg, 2)
        return (data[0] << 8) | data[1]

    @staticmethod
    def _signed(value: int) -> int:
        return value - 0x10000 if value > 0x7FFF else value

    def read(self):
        """Return ``(voltage_v, current_a, power_w)`` measured by the chip."""
        bus_raw = self._read(_REG_BUS)
        voltage = (bus_raw >> 3) * 0.004  # bits 3..15, 4 mV LSB
        current = self._signed(self._read(_REG_SHUNT)) * 0.01 / self.shunt_ohms
        # Bus power register: power_lsb = 20 * current_lsb.
        power = self._read(_REG_POWER) * self._current_lsb * 20
        if not power:
            power = abs(voltage * current)
        return voltage, abs(current), power

    def close(self) -> None:
        try:
            self._bus.close()
        except Exception:
            pass
