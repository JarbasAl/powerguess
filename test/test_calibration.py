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
    monkeypatch.delenv("CALIBRATION_PSU_W", raising=False)
    assert Calibration.from_env() is None


def test_from_psu_bounds():
    cal = Calibration.from_psu(idle_power=2.7, psu_watts=15.0, voltage=5.0)
    assert cal.idle_power == 2.7
    assert cal.load_power == 15.0  # PSU rating is the ceiling
    assert cal.source == "psu-bound"


def test_from_psu_never_below_idle():
    cal = Calibration.from_psu(idle_power=10.0, psu_watts=5.0)
    assert cal.load_power == 10.0  # clamped to idle floor


def test_from_env_psu_fallback(monkeypatch):
    monkeypatch.setenv("CALIBRATION_IDLE_W", "2.7")
    monkeypatch.delenv("CALIBRATION_LOAD_W", raising=False)
    monkeypatch.setenv("CALIBRATION_PSU_W", "15")
    cal = Calibration.from_env()
    assert cal.source == "psu-bound" and cal.load_power == 15.0


def test_auto_calibrator_needs_min_samples():
    ac = AutoCalibrator(min_samples=10)
    for _ in range(3):
        ac.update(Reading(5.0, 5, 1, "battery"))
    assert ac.calibration() is None  # too few samples


def test_auto_calibrator_learns_percentiles():
    ac = AutoCalibrator(min_samples=10)
    # A spread of measured readings; idle≈5th pct, peak≈95th pct.
    for p in [2.5, 2.6, 2.7, 3, 4, 5, 6, 7, 8, 8.8, 9.0]:
        ac.update(Reading(p, 5, p / 5, "battery"))
    cal = ac.calibration()
    assert cal.source == "auto"
    assert 2.4 <= cal.idle_power <= 3.0
    assert 8.5 <= cal.load_power <= 9.0


def test_auto_calibrator_robust_to_outlier():
    ac = AutoCalibrator(min_samples=10)
    # A realistic spread of measured power...
    for p in [3, 3.2, 3.5, 4, 5, 6, 7, 7.5, 7.8, 8] * 3:
        ac.update(Reading(p, 5, p / 5, "battery"))
    # ...plus lone glitches the bounds must ignore.
    ac.update(Reading(0.01, 5, 0, "battery"))
    ac.update(Reading(500.0, 5, 100, "battery"))
    cal = ac.calibration()
    # Bounds track the bulk, not the glitches (abs min/max would catch 0.01/500).
    assert cal.idle_power >= 2.0 and cal.load_power <= 9.0


def test_auto_calibrator_ignores_estimates():
    ac = AutoCalibrator(min_samples=2)
    ac.update(Reading(2.0, 5, 0.4, "estimate", error_margin=1))
    ac.update(Reading(20.0, 5, 4, "estimate", error_margin=5))
    assert ac.calibration() is None  # estimates never move the bounds


def test_auto_calibrator_persists(tmp_path):
    path = str(tmp_path / "cal.json")
    ac = AutoCalibrator(path, save_every=1, min_samples=3)
    for p in [3.0, 6.0, 11.0, 11.0]:
        ac.update(Reading(p, 5, p / 5, "ina219"))
    reloaded = Calibration.load(path)
    assert reloaded is not None and reloaded.source == "auto"
    assert reloaded.load_power > reloaded.idle_power
