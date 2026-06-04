"""PowerGuess — estimate (or measure) the power draw of a Linux device.

A dependency-light power library. :class:`~powerguess.guess.PowerStatMonitor`
picks the best available *whole-device* power source — INA219, Raspberry Pi PMIC
(Pi 5), battery rails, powerstat — and otherwise estimates from CPU load against a
per-device profile. Every sample is a :class:`~powerguess.reading.Reading` that
records its provenance, so a guess is never mistaken for a measurement. A
:class:`~powerguess.calibration.Calibration` pins the estimate to the device;
:class:`~powerguess.calibration.AutoCalibrator` learns it from measured readings.

This package is I/O-bridge free — it computes watts and nothing else. For the
Home Assistant / MQTT bridge and system telemetry (CPU/GPU temperature,
throttling, …) see the companion **linux2mqtt** project, which builds on this.
"""
from powerguess.calibration import AutoCalibrator, Calibration
from powerguess.guess import PowerStatMonitor
from powerguess.reading import Reading
from powerguess.version import __version__

__all__ = [
    "PowerStatMonitor",
    "Reading",
    "Calibration",
    "AutoCalibrator",
    "__version__",
]
