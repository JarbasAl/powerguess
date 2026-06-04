"""Battery-path tests for PowerStatMonitor, with /sys readings mocked."""
import powerguess.guess as guess
from powerguess import PowerStatMonitor

CHARGING = {"capacity": 80, "voltage": 16.9, "current": 0.54, "power": 9.1,
            "charge": 3.5, "status": "Charging", "name": "BAT0", "time_left": -1}
DISCHARGING = dict(CHARGING, status="Discharging", power=12.0)


def _patch_battery(monkeypatch, battery):
    monkeypatch.setattr(guess, "get_battery_info",
                        lambda: iter([battery]) if battery else iter([]))


def test_get_battery(monkeypatch):
    _patch_battery(monkeypatch, CHARGING)
    assert PowerStatMonitor.get_battery()["status"] == "Charging"


def test_get_battery_none(monkeypatch):
    _patch_battery(monkeypatch, None)
    assert PowerStatMonitor.get_battery() is None


def test_battery_consumption_when_charging(monkeypatch):
    _patch_battery(monkeypatch, CHARGING)
    p, v, i = PowerStatMonitor.get_battery_consumption()
    assert p == 9.1
    assert PowerStatMonitor.get_battery_output() == (0, 0, 0)


def test_battery_output_when_discharging(monkeypatch):
    _patch_battery(monkeypatch, DISCHARGING)
    p, v, i = PowerStatMonitor.get_battery_output()
    assert p == 12.0
    assert PowerStatMonitor.get_battery_consumption() == (0, 0, 0)


def test_measure_powerstat_fallback_yields_estimate(monkeypatch):
    # No powerstat binary -> the estimate fallback path must yield a reading.
    monkeypatch.setattr(guess, "find_executable", lambda name: None)
    _patch_battery(monkeypatch, None)
    PowerStatMonitor.set_model("Raspberry Pi 4 Model B")
    m = PowerStatMonitor()
    m.disable_powerstat = None
    readings = list(m.measure_powerstat())
    assert readings and len(readings[0]) == 3
