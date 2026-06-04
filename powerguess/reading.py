"""The power reading data model, carrying its own provenance."""

from __future__ import annotations

import dataclasses

# Whole-device sources, ordered most → least trustworthy. (RAPL is CPU-package
# only, so it is a component in powerguess.cpu, not a total-device source.)
MEASURED_SOURCES = ("ina219", "powerstat", "battery")
ESTIMATED_SOURCE = "estimate"


@dataclasses.dataclass(frozen=True)
class Reading:
    """A single power reading and where it came from.

    :param power: watts.
    :param voltage: volts.
    :param current: amps.
    :param source: ``ina219`` / ``powerstat`` / ``battery`` (measured) or
        ``estimate`` (modelled from CPU load).
    :param error_margin: ± watts. Zero for measured sources; a confidence band
        for estimates so consumers never mistake a guess for a measurement.
    """

    power: float
    voltage: float
    current: float
    source: str
    error_margin: float = 0.0

    @property
    def measured(self) -> bool:
        """True when the reading comes from real hardware, not the estimator."""
        return self.source in MEASURED_SOURCES

    def as_dict(self) -> dict:
        return {
            "power": round(self.power, 3),
            "voltage": round(self.voltage, 3),
            "current": round(self.current, 3),
            "source": self.source,
            "measured": self.measured,
            "error_margin": round(self.error_margin, 3),
        }
