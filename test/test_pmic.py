import powerguess.pmic as pmic
from powerguess.pmic import parse_pmic_adc

PMIC_SAMPLE = """        3V7_WL_SW_A current(0)=0.02500000A
        3V3_SYS_A current(1)=0.40000000A
        VDD_CORE_A current(7)=2.50000000A
        EXT5V_V volt(24)=5.10000000V
        3V3_SYS_V volt(18)=3.30000000V
        VDD_CORE_V volt(7)=0.72000000V
        3V7_WL_SW_V volt(0)=3.70000000V"""


def test_parse_pmic_sums_rail_power():
    # 0.025*3.7 + 0.4*3.3 + 2.5*0.72 = 0.0925 + 1.32 + 1.8 = 3.2125
    assert parse_pmic_adc(PMIC_SAMPLE) == 3.212


def test_parse_pmic_ignores_unpaired_rails():
    assert parse_pmic_adc("        EXT5V_V volt(24)=5.1V") is None


def test_parse_pmic_empty():
    assert parse_pmic_adc("garbage\nno rails here") is None


def test_pmic_available(monkeypatch):
    monkeypatch.setattr(pmic, "pmic_power", lambda: 5.2)   # Pi 5
    assert pmic.pmic_available() is True
    monkeypatch.setattr(pmic, "pmic_power", lambda: None)  # Pi 3/4
    assert pmic.pmic_available() is False
