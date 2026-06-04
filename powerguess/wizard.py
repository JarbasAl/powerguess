"""Guided calibration: measure a device with a smart plug over MQTT.

``powerguess-calibrate`` walks you through measuring your device's real idle and
peak power using any MQTT smart plug (Tasmota, Shelly, ESPHome, Zigbee2MQTT, …)
as the meter, then writes a ``calibration.json`` PowerGuess can use. The plug is
ground truth; the wizard just reads it while prompting you to idle the device and
then load it.

The MQTT/parsing helpers and the number-crunching are importable and tested; the
``run()`` flow is the thin interactive layer.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from collections import deque
from shutil import which
from typing import List, Optional

from .calibration import Calibration

LOG = logging.getLogger("powerguess.wizard")


# --- payload parsing (pure) ----------------------------------------------------

def _walk(data, dotted: str):
    """Follow a dotted path through nested dicts, case-insensitively."""
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        if part in cur:
            cur = cur[part]
            continue
        lowered = {k.lower(): k for k in cur}
        if part.lower() in lowered:
            cur = cur[lowered[part.lower()]]
        else:
            return None
    return cur


def parse_power(payload: str, key: Optional[str] = None) -> Optional[float]:
    """Extract watts from an MQTT payload.

    A bare number is used directly. Otherwise the payload is parsed as JSON and
    ``key`` (a dotted path like ``ENERGY.Power``) is read; with no key, common
    power fields are tried.
    """
    payload = (payload or "").strip()
    if not payload:
        return None
    if key:
        try:
            value = _walk(json.loads(payload), key)
            if value is not None:
                return float(value)
        except (ValueError, TypeError):
            pass
    try:
        return float(payload)
    except ValueError:
        pass
    try:
        data = json.loads(payload)
    except ValueError:
        return None
    for candidate in ("ENERGY.Power", "power", "Power", "apower", "watts", "W"):
        value = _walk(data, candidate)
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                continue
    return None


# --- sample summarising (pure) -------------------------------------------------

def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, max(0, int(round((pct / 100.0) * (len(s) - 1)))))
    return s[idx]


def summarise(samples: List[float]) -> dict:
    """Return median / min / p90 / max of a sample window."""
    clean = [s for s in samples if s is not None]
    if not clean:
        return {"n": 0, "median": 0.0, "min": 0.0, "p90": 0.0, "max": 0.0}
    return {
        "n": len(clean),
        "median": round(statistics.median(clean), 2),
        "min": round(min(clean), 2),
        "p90": round(_percentile(clean, 90), 2),
        "max": round(max(clean), 2),
    }


def build_calibration(idle_samples: List[float], load_samples: List[float],
                      voltage: float = 230.0,
                      psu_watts: Optional[float] = None) -> tuple:
    """Build a Calibration from measured windows; return (calibration, warnings).

    Idle uses the median (stable resting draw); load uses the 90th percentile
    (sustained peak, ignoring one-off spikes).
    """
    idle = summarise(idle_samples)
    load = summarise(load_samples)
    warnings: List[str] = []
    if idle["n"] == 0 or load["n"] == 0:
        warnings.append("no plug readings captured — is the power topic correct?")
        return None, warnings

    idle_w = idle["median"]
    load_w = load["p90"]
    if load_w <= idle_w:
        warnings.append("load power is not above idle — did the stress command run?")
    if psu_watts and load_w > psu_watts:
        warnings.append(f"measured peak {load_w} W exceeds the PSU rating "
                        f"{psu_watts} W — check the rating or the meter")
    if psu_watts and load_w < psu_watts * 0.1:
        warnings.append(f"measured peak {load_w} W is under 10% of the {psu_watts} W "
                        f"PSU — the plug may be reporting standby only")

    cal = Calibration(idle_power=idle_w, load_power=max(load_w, idle_w),
                      voltage=voltage, source="manual")
    return cal, warnings


# --- MQTT meter ----------------------------------------------------------------

class MQTTPowerMeter:
    """Subscribe to a smart-plug power topic and expose the latest watts."""

    def __init__(self, host: str, port: int, topic: str, key: Optional[str] = None,
                 user: Optional[str] = None, password: Optional[str] = None,
                 client=None):
        import paho.mqtt.client as mqtt
        self.topic = topic
        self.key = key
        self._latest: Optional[float] = None
        self._buf: deque = deque(maxlen=600)
        self._host, self._port = host, port
        self.client = client or mqtt.Client(client_id="powerguess-calibrate")
        if client is None and user and password:
            self.client.username_pw_set(user, password)
        self.client.on_message = self._on_message

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
        except Exception:
            return
        watts = parse_power(payload, self.key)
        if watts is not None:
            self._latest = watts
            self._buf.append(watts)

    def connect(self) -> None:
        self.client.connect(self._host, self._port)
        self.client.subscribe(self.topic)
        self.client.loop_start()

    def disconnect(self) -> None:
        try:
            self.client.loop_stop()
        except Exception:
            pass
        self.client.disconnect()

    def latest(self) -> Optional[float]:
        return self._latest

    def wait_for_reading(self, timeout: float = 15.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._latest is not None:
                return True
            time.sleep(0.25)
        return False

    def sample(self, seconds: float, on_tick=None) -> List[float]:
        """Collect the latest reading once per second for ``seconds``."""
        out: List[float] = []
        for remaining in range(int(seconds), 0, -1):
            if self._latest is not None:
                out.append(self._latest)
            if on_tick:
                on_tick(remaining, self._latest)
            time.sleep(1.0)
        return out


# --- interactive flow ----------------------------------------------------------

def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def _suggest_load_command() -> str:
    if which("stress-ng"):
        return "stress-ng --cpu $(nproc) --timeout 40s"
    if which("stress"):
        return "stress --cpu $(nproc) --timeout 40s"
    return "for i in $(seq $(nproc)); do yes > /dev/null & done   # Ctrl-C / kill %1.. to stop"


def run() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    from .config import Config

    print("PowerGuess calibration wizard")
    print("Measure your device with an MQTT smart plug, then save a calibration.\n")

    host = _ask("MQTT broker host", Config.MQTT_HOST)
    port = int(_ask("MQTT broker port", str(Config.MQTT_PORT)))
    user = _ask("MQTT username (blank for none)", Config.MQTT_USER or "")
    password = _ask("MQTT password (blank for none)", Config.MQTT_PASSWORD or "")
    topic = _ask("Smart-plug power topic", "tele/plug/SENSOR")
    key = _ask("JSON key for watts (blank if the payload is a bare number)",
               "ENERGY.Power")
    voltage = float(_ask("Supply voltage (230 mains EU, 120 mains US, 5 USB)", "230"))
    psu_raw = _ask("PSU rated watts (optional, for a sanity check)", "")
    psu_watts = float(psu_raw) if psu_raw else None

    meter = MQTTPowerMeter(host, port, topic, key=key,
                           user=user or None, password=password or None)
    print(f"\nConnecting to {host}:{port}, listening on {topic} …")
    try:
        meter.connect()
    except Exception as exc:  # noqa: BLE001
        print(f"could not connect to MQTT: {exc}")
        return 1

    if not meter.wait_for_reading():
        print("No power readings arrived. Check the topic and that the plug is "
              "publishing, then re-run.")
        meter.disconnect()
        return 1
    print(f"Reading the plug: {meter.latest()} W now.\n")

    def tick(remaining, value):
        print(f"  {remaining:2d}s … {value} W   ", end="\r", flush=True)

    input("STEP 1/2 — idle (the floor). Leave the device idle and quiet, then press Enter …")
    idle_samples = meter.sample(20, tick)
    idle_summary = summarise(idle_samples)
    print(f"\n  idle ≈ {idle_summary['median']} W  (the lower bound)\n")

    # Peak is the ceiling. Measure it for a tight bound, or fall back to the PSU
    # rating for a loose-but-valid one (see docs/theory.md).
    can_load = _ask("STEP 2/2 — can you put the device under full load now? [Y/n]",
                    "Y").lower() not in ("n", "no")
    if can_load:
        print("In another terminal, run e.g.:")
        print(f"    {_suggest_load_command()}")
        input("Start the load, wait a few seconds, then press Enter …")
        load_samples = meter.sample(20, tick)
        print(f"\n  peak ≈ {summarise(load_samples)['p90']} W  (the upper bound)\n")
        meter.disconnect()
        cal, warnings = build_calibration(idle_samples, load_samples,
                                          voltage=voltage, psu_watts=psu_watts)
    else:
        meter.disconnect()
        if idle_summary["n"] == 0:
            print("  ! no idle readings captured — check the power topic.")
            return 1
        if not psu_watts:
            psu_raw = _ask("Enter the PSU rated watts to use as the upper bound", "")
            psu_watts = float(psu_raw) if psu_raw else None
        if not psu_watts:
            print("  ! need either a load test or a PSU rating to set the upper bound.")
            return 1
        cal = Calibration.from_psu(idle_summary["median"], psu_watts, voltage)
        warnings = ["upper bound is the PSU rating (loose) — run a load test later "
                    "for a tighter estimate"]
        print(f"\n  ceiling = PSU rating {psu_watts} W  (loose upper bound)\n")

    for w in warnings:
        print(f"  ! {w}")
    if cal is None:
        return 1

    out = _ask("Save calibration to", Config.CALIBRATION_FILE or "calibration.json")
    cal.save(out)
    print(f"\nSaved {out}:")
    print(f"  idle {cal.idle_power} W   peak {cal.load_power} W   ({voltage} V)")
    print(f"\nUse it:  CALIBRATION_FILE={out} python -m powerguess")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
