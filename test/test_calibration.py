import os
import tempfile

from powerguess.calibration import AutoCalibrator, Calibration
from powerguess.reading import Reading


def test_benchmarks_from_calibration():
    cal = Calibration(idle_power=3.0, load_power=10.0, voltage=5.0)
    b = cal.benchmarks()
    assert b["idle"]["power"] == 3.0
    assert b["load"]["power"] == 10.0
    assert b["avg"]["power"] == 6.5
    assert b["idle"]["current"] == 3.0 / 5.0


def test_roundtrip_file():
    cal = Calibration(idle_power=2.0, load_power=8.0, voltage=12.0, source="manual")
    path = tempfile.mktemp(suffix=".json")
    cal.save(path)
    loaded = Calibration.load(path)
    assert loaded == cal
    os.remove(path)


def test_load_missing_returns_none():
    assert Calibration.load("/no/such/file.json") is None


def test_from_env(monkeypatch):
    monkeypatch.setenv("CALIBRATION_IDLE_W", "2.5")
    monkeypatch.setenv("CALIBRATION_LOAD_W", "9.5")
    cal = Calibration.from_env()
    assert cal.idle_power == 2.5 and cal.load_power == 9.5 and cal.source == "manual"


def test_from_env_absent(monkeypatch):
    monkeypatch.delenv("CALIBRATION_IDLE_W", raising=False)
    monkeypatch.delenv("CALIBRATION_LOAD_W", raising=False)
    assert Calibration.from_env() is None


def test_auto_calibrator_learns_from_measured():
    ac = AutoCalibrator()
    assert ac.calibration() is None
    ac.update(Reading(2.5, 5, 0.5, "battery"))
    ac.update(Reading(9.0, 5, 1.8, "battery"))
    ac.update(Reading(4.0, 5, 0.8, "battery"))
    cal = ac.calibration()
    assert cal.idle_power == 2.5 and cal.load_power == 9.0 and cal.source == "auto"


def test_auto_calibrator_ignores_estimates():
    ac = AutoCalibrator()
    ac.update(Reading(2.0, 5, 0.4, "estimate", error_margin=1))
    ac.update(Reading(20.0, 5, 4, "estimate", error_margin=5))
    assert ac.calibration() is None  # estimates never move the bounds


def test_auto_calibrator_persists(tmp_path):
    path = str(tmp_path / "cal.json")
    ac = AutoCalibrator(path, save_every=1)
    ac.update(Reading(3.0, 5, 0.6, "ina219"))
    ac.update(Reading(11.0, 5, 2.2, "ina219"))
    reloaded = Calibration.load(path)
    assert reloaded is not None and reloaded.source == "auto"
    assert reloaded.idle_power == 3.0 and reloaded.load_power == 11.0
