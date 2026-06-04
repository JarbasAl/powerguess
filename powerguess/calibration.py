"""Per-device calibration for the power estimate.

The generic per-model benchmark profiles are coarse. A calibration pins the
estimate to the user's actual device with just two numbers — idle and peak watts
— which beats any generic profile. Calibrations can be supplied by hand
(env / file) or learned automatically from a measured source over time.
"""

from __future__ import annotations

import dataclasses
import json
import os
from collections import deque
from typing import Optional

from .reading import Reading


@dataclasses.dataclass
class Calibration:
    """Idle and peak power for one device, used to build the estimate curve.

    :param source: ``manual`` (user supplied) or ``auto`` (learned from
        measured readings).
    """

    idle_power: float
    load_power: float
    voltage: float = 5.0
    idle_current: Optional[float] = None
    load_current: Optional[float] = None
    source: str = "manual"

    def benchmarks(self) -> dict:
        """Render the idle/avg/load profile the estimator consumes."""
        v = self.voltage or 5.0
        ic = self.idle_current if self.idle_current is not None else self.idle_power / v
        lc = self.load_current if self.load_current is not None else self.load_power / v
        avg_p = (self.idle_power + self.load_power) / 2
        return {
            "idle": {"power": self.idle_power, "voltage": v, "current": ic},
            "avg": {"power": avg_p, "voltage": v, "current": (ic + lc) / 2},
            "load": {"power": self.load_power, "voltage": v, "current": lc},
        }

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Calibration":
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> Optional["Calibration"]:
        if not path or not os.path.isfile(path):
            return None
        with open(path) as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def from_psu(cls, idle_power: float, psu_watts: float,
                 voltage: float = 5.0) -> "Calibration":
        """Bound the estimate by measured idle (floor) and PSU rating (ceiling).

        The PSU rating is a hard but loose upper bound — real peak draw is
        usually well below it — so the estimate is conservative and its error
        band wide. A measured peak (the load test) gives a tighter ceiling.
        """
        return cls(idle_power=idle_power, load_power=max(psu_watts, idle_power),
                   voltage=voltage, source="psu-bound")

    @classmethod
    def from_env(cls) -> Optional["Calibration"]:
        idle = os.getenv("CALIBRATION_IDLE_W")
        load = os.getenv("CALIBRATION_LOAD_W")
        psu = os.getenv("CALIBRATION_PSU_W")
        voltage = float(os.getenv("CALIBRATION_VOLTAGE", "5.0"))
        if idle and load:
            return cls(idle_power=float(idle), load_power=float(load),
                       voltage=voltage, source="manual")
        # Fall back to bounding by the PSU rating when no measured peak is given.
        if idle and psu:
            return cls.from_psu(float(idle), float(psu), voltage)
        return None


class AutoCalibrator:
    """Learn idle/peak power from measured readings and persist it.

    Keeps a rolling window of *measured* power (ground truth) and reads the idle
    floor and peak ceiling off its 5th / 95th percentiles — robust to the odd
    glitch or spike that absolute min/max would latch onto. Once enough samples
    are in, it yields an ``auto`` calibration future runs reuse, so the estimate
    sharpens itself on hardware that has a meter for at least part of its life.
    """

    def __init__(self, path: Optional[str] = None, save_every: int = 20,
                 window: int = 500, min_samples: int = 10,
                 low_pct: float = 5.0, high_pct: float = 95.0):
        self.path = path
        self.save_every = save_every
        self.min_samples = min_samples
        self.low_pct = low_pct
        self.high_pct = high_pct
        self._samples: deque = deque(maxlen=window)
        self._voltage: float = 5.0
        self._dirty = 0
        existing = Calibration.load(path) if path else None
        if existing and existing.source == "auto":
            # Seed the window with the persisted bounds so we don't start cold.
            self._samples.extend([existing.idle_power, existing.load_power])
            self._voltage = existing.voltage

    @staticmethod
    def _percentile(values: list, pct: float) -> float:
        s = sorted(values)
        idx = min(len(s) - 1, max(0, int(round((pct / 100.0) * (len(s) - 1)))))
        return s[idx]

    def update(self, reading: Reading) -> None:
        """Fold one reading in. Only measured readings move the bounds."""
        if not reading.measured or reading.power <= 0:
            return
        self._samples.append(reading.power)
        if reading.voltage:
            self._voltage = reading.voltage
        self._dirty += 1
        if self.path and self._dirty >= self.save_every and self.calibration():
            self.calibration().save(self.path)
            self._dirty = 0

    def calibration(self) -> Optional[Calibration]:
        if len(self._samples) < self.min_samples:
            return None
        vals = list(self._samples)
        idle = round(self._percentile(vals, self.low_pct), 3)
        load = round(self._percentile(vals, self.high_pct), 3)
        if load <= idle:
            return None
        return Calibration(idle_power=idle, load_power=load,
                           voltage=self._voltage, source="auto")
