from powerguess import PowerStatMonitor


def test_set_model_loads_pi4_benchmarks():
    PowerStatMonitor.set_model("Raspberry Pi 4 Model B")
    assert set(PowerStatMonitor.benchmarks) == {"idle", "avg", "load"}
    assert PowerStatMonitor.benchmarks["load"]["power"] == 6.4


def test_set_model_generic_fallback():
    PowerStatMonitor.set_model("")  # unidentifiable -> a generic profile
    assert "idle" in PowerStatMonitor.benchmarks
    assert "load" in PowerStatMonitor.benchmarks


def test_guesstimate_returns_triple():
    PowerStatMonitor.set_model("Raspberry Pi 4 Model B")
    p, v, i = PowerStatMonitor.guesstimate()
    assert all(isinstance(x, (int, float)) for x in (p, v, i))
    # Power stays within the model's idle..load envelope (plus battery charge).
    assert 0 <= p <= 50


def test_monitor_instantiates_and_loads_model():
    m = PowerStatMonitor()
    assert PowerStatMonitor.benchmarks  # a profile is always loaded
    assert isinstance(m.has_battery, bool)
