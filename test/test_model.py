import json
import tempfile

from powerguess.model import FEATURES, LinearPredictor, current_features


def test_current_features_keys():
    feats = current_features()
    assert set(FEATURES).issubset(feats)
    assert feats["n_cores"] >= 1


def test_linear_predictor_dot_product():
    pred = LinearPredictor({"cpu_percent": 0.1, "n_cores": 0.5}, intercept=2.0)
    watts = pred.predict({"cpu_percent": 50, "n_cores": 4})
    assert watts == 2.0 + 0.1 * 50 + 0.5 * 4


def test_linear_predictor_never_negative():
    pred = LinearPredictor({"cpu_percent": -1.0}, intercept=0.0)
    assert pred.predict({"cpu_percent": 100}) == 0.0


def test_linear_predictor_load():
    path = tempfile.mktemp(suffix=".json")
    with open(path, "w") as f:
        json.dump({"intercept": 1.0, "coefficients": {"cpu_percent": 0.05}}, f)
    pred = LinearPredictor.load(path)
    assert pred.predict({"cpu_percent": 20}) == 2.0
