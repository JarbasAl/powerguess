import powerguess.guess as guess
from powerguess import Calibration, PowerStatMonitor
from powerguess.reading import Reading


def _monitor():
    # Disable powerstat so measure() is deterministic in CI.
    return PowerStatMonitor(use_powerstat=False)


def test_set_model_loads_pi4_benchmarks():
    m = _monitor()
    m.set_model("Raspberry Pi 4 Model B")
    assert set(m.benchmarks) == {"idle", "avg", "load"}
    assert m.benchmarks["load"]["power"] == 6.4


def test_generic_fallback_profile():
    m = _monitor()
    m.set_model("")
    assert "idle" in m.benchmarks and "load" in m.benchmarks


def test_calibration_overrides_profile():
    cal = Calibration(idle_power=3.0, load_power=10.0, voltage=5.0)
    m = PowerStatMonitor(use_powerstat=False, calibration=cal)
    assert m.benchmarks["idle"]["power"] == 3.0
    assert m.benchmarks["load"]["power"] == 10.0


def test_estimate_is_monotonic(monkeypatch):
    m = _monitor()
    m.set_model("Raspberry Pi 4 Model B")
    pmin = m.benchmarks["idle"]["power"]
    pmax = m.benchmarks["load"]["power"]
    monkeypatch.setattr(guess.psutil, "cpu_percent", lambda: 0)
    p0, _, _ = m.estimate()
    monkeypatch.setattr(guess.psutil, "cpu_percent", lambda: 100)
    p100, _, _ = m.estimate()
    assert abs(p0 - pmin) < 0.01
    assert abs(p100 - pmax) < 0.01
    assert p0 < p100


def test_measure_returns_reading_with_provenance():
    m = _monitor()
    r = m.measure()
    assert isinstance(r, Reading)
    # No INA219, no battery discharge, no powerstat -> estimate with a band.
    if not r.measured:
        assert r.source == "estimate" and r.error_margin > 0


def test_predictor_path(monkeypatch):
    from powerguess.model import LinearPredictor
    pred = LinearPredictor({"cpu_percent": 0.1}, intercept=2.0)
    m = PowerStatMonitor(use_powerstat=False, predictor=pred)
    monkeypatch.setattr(guess.psutil, "cpu_percent", lambda: 50)
    p, v, i = m.estimate()
    assert p == 2.0 + 0.1 * 50


def test_energy_integration():
    import time
    m = _monitor()
    now = time.time()
    m._integrate_energy(Reading(10, 5, 2, "estimate"), now)
    m._integrate_energy(Reading(10, 5, 2, "estimate"), now + 3600)
    assert round(m.energy_wh, 2) == 10.0  # 10 W for 1 h = 10 Wh


def test_instance_state_isolated():
    a = _monitor()
    b = _monitor()
    a.add_callback(lambda r: None)
    assert a.callbacks is not b.callbacks  # no shared class-level state
    assert len(b.callbacks) == 0
