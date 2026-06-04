"""Collect a (device features → measured watts) dataset.

Runs PowerGuess and, whenever a **measured** reading is available (INA219,
powerstat/RAPL, or battery discharge), appends a row pairing the current device
features with the true wattage. Aggregated across contributors who have a meter,
this is the training corpus for the power-prediction model — see
``docs/dataset.md``.

    python dataset.py --out powerguess.jsonl --samples 500

Rows are JSONL: ``{ts, arch, model, cpu_percent, cpu_freq_mhz, n_cores,
has_battery, source, watts}``. Devices with no measured source produce nothing
(estimates are never written — that would poison the dataset).
"""

from __future__ import annotations

import argparse
import json
import threading
import time

from powerguess.guess import PowerStatMonitor
from powerguess.model import current_features, device_arch


def collect(out_path: str, samples: int = 0, interval: float = 5.0) -> int:
    monitor = PowerStatMonitor(time_between_measures=interval)
    arch = device_arch()
    written = 0
    done = threading.Event()

    with open(out_path, "a") as fh:
        def on_reading(reading):
            nonlocal written
            if not reading.measured:
                return  # only ground-truth rows
            row = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "arch": arch,
                "model": monitor.model or "unknown",
                **current_features(monitor),
                "source": reading.source,
                "watts": round(reading.power, 3),
            }
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            written += 1
            print(f"[{written}] {reading.source}: {reading.power:.2f} W")
            if samples and written >= samples:
                done.set()

        monitor.add_callback(on_reading)
        monitor.start()
        try:
            done.wait()
        except KeyboardInterrupt:
            pass
        finally:
            monitor.stop()
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="Collect a power dataset from a measured source.")
    ap.add_argument("--out", default="powerguess.jsonl", help="output JSONL path")
    ap.add_argument("--samples", type=int, default=0, help="stop after N rows (0 = until Ctrl-C)")
    ap.add_argument("--interval", type=float, default=5.0, help="seconds between samples")
    args = ap.parse_args()
    n = collect(args.out, samples=args.samples, interval=args.interval)
    print(f"wrote {n} rows to {args.out}")
    if n == 0:
        print("no measured source on this device — nothing collected (this is expected "
              "without INA219 / powerstat / a discharging battery).")


if __name__ == "__main__":
    main()
