"""Pluggable power predictor and the feature vector it shares with the dataset.

The default estimate is the calibrated idle/load curve in
:meth:`PowerStatMonitor.estimate`. This module adds an optional, richer path: a
small linear model over device features (CPU load, frequency, core count, …)
loaded from a JSON of coefficients. A model is trained from the corpus the
:mod:`powerguess.dataset` collector gathers on devices that have a meter — see
``docs/dataset.md``. No heavy ML dependency: prediction is a pure-Python dot
product, so a trained model ships as plain JSON.
"""

from __future__ import annotations

import json
import os
import platform
from typing import Dict, Optional

import psutil

from .utils import read_cpu_temp

# The ordered feature names a model expects; the dataset collector emits the same.
FEATURES = ["cpu_percent", "cpu_freq_mhz", "n_cores", "load_avg_1m",
            "cpu_temp_c", "has_battery"]


def current_features(monitor=None) -> Dict[str, float]:
    """Snapshot the current device features used for prediction / dataset rows."""
    freq = psutil.cpu_freq()
    has_battery = bool(getattr(monitor, "has_battery", False))
    try:
        load1 = os.getloadavg()[0]
    except (OSError, AttributeError):
        load1 = 0.0
    return {
        "cpu_percent": float(psutil.cpu_percent()),
        "cpu_freq_mhz": float(freq.current) if freq else 0.0,
        "n_cores": float(psutil.cpu_count() or 1),
        "load_avg_1m": float(load1),
        "cpu_temp_c": read_cpu_temp(),
        "has_battery": 1.0 if has_battery else 0.0,
    }


def device_arch() -> str:
    return platform.machine()


class LinearPredictor:
    """watts = intercept + Σ coef_i · feature_i.

    :param coefficients: ``{feature_name: weight}``.
    :param intercept: constant term (watts).
    """

    def __init__(self, coefficients: Dict[str, float], intercept: float = 0.0):
        self.coefficients = coefficients
        self.intercept = intercept

    def predict(self, features: Dict[str, float]) -> float:
        watts = self.intercept
        for name, coef in self.coefficients.items():
            watts += coef * features.get(name, 0.0)
        return max(0.0, watts)

    @classmethod
    def load(cls, path: str) -> Optional["LinearPredictor"]:
        """Load a model JSON ``{"intercept": .., "coefficients": {..}}``."""
        if not path:
            return None
        with open(path) as f:
            data = json.load(f)
        return cls(coefficients=data.get("coefficients", {}),
                   intercept=float(data.get("intercept", 0.0)))
