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
    def from_env(cls) -> Optional["Calibration"]:
        idle = os.getenv("CALIBRATION_IDLE_W")
        load = os.getenv("CALIBRATION_LOAD_W")
        if idle and load:
            return cls(idle_power=float(idle), load_power=float(load),
                       voltage=float(os.getenv("CALIBRATION_VOLTAGE", "5.0")),
                       source="manual")
        return None


class AutoCalibrator:
    """Learn idle/peak power from measured readings and persist it.

    Tracks the lowest and highest *measured* power seen (a measured source is
    ground truth) and, once both ends are known, yields an ``auto`` calibration
    that future runs reuse — so the estimate sharpens itself on hardware that has
    a meter for at least part of its life.
    """

    def __init__(self, path: Optional[str] = None, save_every: int = 20):
        self.path = path
        self.save_every = save_every
        self._idle: Optional[float] = None
        self._load: Optional[float] = None
        self._voltage: float = 5.0
        self._dirty = 0
        existing = Calibration.load(path) if path else None
        if existing and existing.source == "auto":
            self._idle, self._load, self._voltage = (
                existing.idle_power, existing.load_power, existing.voltage)

    def update(self, reading: Reading) -> None:
        """Fold one reading in. Only measured readings move the bounds."""
        if not reading.measured or reading.power <= 0:
            return
        p = reading.power
        if self._idle is None or p < self._idle:
            self._idle = p
            self._dirty += 1
        if self._load is None or p > self._load:
            self._load = p
            self._dirty += 1
        if reading.voltage:
            self._voltage = reading.voltage
        if self.path and self._dirty >= self.save_every and self.calibration():
            self.calibration().save(self.path)
            self._dirty = 0

    def calibration(self) -> Optional[Calibration]:
        if self._idle is None or self._load is None or self._load <= self._idle:
            return None
        return Calibration(idle_power=self._idle, load_power=self._load,
                           voltage=self._voltage, source="auto")
