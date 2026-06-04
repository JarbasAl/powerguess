"""PowerGuess — estimate the live power draw of a Linux device.

The core :class:`~powerguess.guess.PowerStatMonitor` reads ``powerstat`` when
available, falls back to a per-model CPU-load estimate, and reads battery rails
directly from ``/sys/class/power_supply``. It has no Home Assistant or OVOS
dependency.

Two integrations live alongside it:

- :mod:`powerguess.mqtt_client` / ``python -m powerguess`` — publish readings to
  MQTT with Home Assistant auto-discovery (the recommended path).
- :mod:`powerguess.sensors` / :mod:`powerguess.device` — the OVOS PHAL sensor
  integration, available with the ``phal`` extra.
"""
from powerguess.guess import PowerStatMonitor
from powerguess.version import __version__

__all__ = ["PowerStatMonitor", "__version__"]
