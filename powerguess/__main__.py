"""CLI entry point: stream power readings to MQTT / Home Assistant."""

from __future__ import annotations

import logging
import signal
import sys
import time
from typing import Any

from .config import Config
from .guess import PowerStatMonitor
from .mqtt_client import MQTTClient
from .utils import get_battery_info
from .version import __version__

LOG = logging.getLogger("powerguess")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
    )


def main() -> None:
    setup_logging()
    LOG.info("powerguess %s starting", __version__)

    monitor = PowerStatMonitor(smooth=Config.SMOOTH,
                               time_between_measures=Config.MEASURE_INTERVAL)
    monitor.prefer_battery = Config.PREFER_BATTERY

    mqtt_client = MQTTClient(has_battery=monitor.has_battery)
    mqtt_client.connect()
    mqtt_client.publish_model(PowerStatMonitor.model)

    def on_reading(reading, model):
        power, voltage, current = reading
        if mqtt_client.publish_reading(power, voltage, current):
            LOG.debug("published %.2f W / %.3f A / %.2f V", power, current, voltage)
            if monitor.has_battery:
                battery = PowerStatMonitor.get_battery()
                mqtt_client.publish_battery(battery)

    monitor.add_callback(on_reading)

    def _shutdown(signum: int, frame: Any) -> None:
        LOG.info("Received signal %s, shutting down", signum)
        monitor.stop()
        mqtt_client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    monitor.start()
    LOG.info("powerguess running — model %r, battery=%s",
             PowerStatMonitor.model or "generic", monitor.has_battery)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        _shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()
