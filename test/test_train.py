import json

from powerguess.model import LinearPredictor
from train import _rmse, fit, load_rows


def _synthetic(n=200):
    # Independent features so coefficients are identifiable:
    # watts = 1.5 + 0.05*cpu + 0.7*cores
    import random
    rng = random.Random(1)
    rows = []
    for _ in range(n):
        cpu = rng.uniform(0, 100)
        cores = rng.choice([1, 2, 4, 8])
        watts = 1.5 + 0.05 * cpu + 0.7 * cores
        rows.append({"cpu_percent": cpu, "n_cores": cores, "cpu_freq_mhz": 0,
                     "load_avg_1m": 0, "cpu_temp_c": 0, "has_battery": 0,
                     "watts": watts})
    return rows


def test_fit_recovers_coefficients():
    model = fit(_synthetic())
    assert abs(model["intercept"] - 1.5) < 0.1
    assert abs(model["coefficients"]["cpu_percent"] - 0.05) < 0.01
    assert abs(model["coefficients"]["n_cores"] - 0.7) < 0.05
    assert _rmse(_synthetic(), model) < 0.1


def test_fit_feeds_predictor():
    model = fit(_synthetic())
    pred = LinearPredictor(model["coefficients"], model["intercept"])
    watts = pred.predict({"cpu_percent": 100, "n_cores": 4})
    assert abs(watts - (1.5 + 5.0 + 2.8)) < 0.3


def test_load_rows_filters_arch(tmp_path):
    path = tmp_path / "d.jsonl"
    path.write_text(
        json.dumps({"arch": "x86_64", "watts": 5, "cpu_percent": 10}) + "\n" +
        json.dumps({"arch": "aarch64", "watts": 3, "cpu_percent": 10}) + "\n")
    assert len(load_rows(str(path))) == 2
    assert len(load_rows(str(path), arch="aarch64")) == 1
