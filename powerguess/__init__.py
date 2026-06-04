"""PowerGuess — estimate (or measure) the live power draw of a Linux device.

:class:`~powerguess.guess.PowerStatMonitor` picks the best available source —
INA219, powerstat/RAPL, battery rails, or a CPU-load estimate — and reports each
sample as a :class:`~powerguess.reading.Reading` that records its provenance, so
a guess is never mistaken for a measurement. A :class:`~powerguess.calibration.Calibration`
pins the estimate to the user's device, and the :class:`~powerguess.calibration.AutoCalibrator`
learns it from measured readings over time.

:mod:`powerguess.mqtt_client` / ``python -m powerguess`` publishes readings to
MQTT with Home Assistant auto-discovery. No Home Assistant or OVOS dependency.
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
