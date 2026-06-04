"""PowerStatMonitor — pick the best available power source and report it.

Source priority, most → least trustworthy:

1. **INA219** I²C power monitor (measured, exact) — see :mod:`powerguess.ina219`.
2. **powerstat** RAPL on x86 (measured) — when installed and privileged.
3. **Battery** discharge rails from ``/sys`` (measured) — laptops on battery.
4. **Estimate** from CPU load against a calibrated idle/load curve.

Every reading is a :class:`~powerguess.reading.Reading` that records its
``source`` and, for estimates, an ``error_margin`` — so a guess is never mistaken
for a measurement. Measured readings also feed the :class:`AutoCalibrator`, which
sharpens future estimates.
"""
import json
import os
import platform
import threading
import time
from itertools import islice
from shutil import which as find_executable
from statistics import mean
from typing import Callable, List, Optional

import pexpect
import psutil

from powerguess import rpi
from powerguess.calibration import AutoCalibrator, Calibration
from powerguess.reading import Reading
from powerguess.utils import get_battery_info, get_model, transform_range

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def _profile_for(model: str) -> str:
    """Map a device model string to a bundled benchmark profile filename."""
    if "Raspberry Pi 4" in model:
        return "pi4.json"
    if "Raspberry Pi 3 Model B Plus" in model:
        return "pi3bplus.json"
    if "Raspberry Pi 3" in model:
        return "pi3b.json"
    if "Raspberry Pi 2" in model:
        return "pi2b.json"
    if "Raspberry Pi Zero" in model:
        return "pi0.json"
    if "U500-H" in model:
        return "minipc_generic.json"
    if platform.machine() == "x86_64" and list(get_battery_info()):
        return "laptop_generic.json"
    if platform.machine() == "aarch64" or "Raspberry Pi" in model:
        return "sbc_generic.json"
    return "pc_generic.json"


class PowerStatMonitor(threading.Thread):
    """Background thread that samples power and fans readings out to callbacks."""

    def __init__(self, smooth: bool = False, time_between_measures: float = 5,
                 calibration: Optional[Calibration] = None,
                 auto_calibrator: Optional[AutoCalibrator] = None,
                 ina219=None, pmic: bool = False, predictor=None,
                 prefer_battery: bool = False, use_powerstat: bool = True,
                 energy_file: Optional[str] = None):
        super().__init__(daemon=True)
        self.smooth = smooth
        self.time_between_measures = time_between_measures
        self.prefer_battery = prefer_battery
        self.use_powerstat = bool(use_powerstat and find_executable("powerstat"))
        self.model = get_model() or ""
        self.benchmarks: dict = {}
        self.callbacks: List[Callable[[Reading], None]] = []
        self.readings: List[float] = []
        self.current: Optional[Reading] = None
        self.running = False
        self._last_ts: Optional[float] = None
        self.has_battery = bool(self.get_battery())
        self.ina = ina219
        self.pmic = pmic
        self.predictor = predictor
        self.calibration = calibration
        self.auto = auto_calibrator
        self.energy_file = energy_file
        self.energy_wh = self._load_energy()
        self._energy_dirty = 0
        self._load_profile()

    # --- benchmark profile / calibration -------------------------------------

    def _load_profile(self) -> None:
        self.set_model(self.model)
        cal = self.calibration or (self.auto.calibration() if self.auto else None)
        if cal:
            self.benchmarks = cal.benchmarks()

    def set_model(self, model: str) -> None:
        """Load the generic benchmark profile for ``model`` into ``benchmarks``."""
        self.model = model
        with open(os.path.join(MODELS_DIR, _profile_for(model or ""))) as f:
            self.benchmarks = json.load(f)

    def add_callback(self, cb: Callable[[Reading], None]) -> None:
        self.callbacks.append(cb)

    # --- battery (measured when discharging) ---------------------------------

    def get_battery(self) -> Optional[dict]:
        bat = list(get_battery_info())
        return bat[0] if bat else None

    def get_battery_output(self):
        """Power drawn *from* the battery while discharging — the device input."""
        bat = self.get_battery()
        if bat and bat["status"] == "Discharging":
            return bat["power"], bat["voltage"], bat["current"]
        return 0, 0, 0

    def get_battery_consumption(self):
        """Extra power going *into* the battery while charging."""
        bat = self.get_battery()
        if bat and bat["status"] == "Charging":
            return bat["power"], bat["voltage"], bat["current"]
        return 0, 0, 0

    # --- estimate -------------------------------------------------------------

    def estimate(self):
        """Estimate (power, voltage, current) from CPU load or a predictor."""
        v = (self.benchmarks["avg"].get("voltage")
             or self.benchmarks["idle"].get("voltage") or 5)
        if self.predictor is not None:
            from powerguess.model import current_features
            p = self.predictor.predict(current_features(self))
            return p, v, (p / v if v else 0)

        cpu = psutil.cpu_percent()
        pmin = self.benchmarks["idle"]["power"]
        pavg = self.benchmarks["avg"]["power"]
        pmax = self.benchmarks["load"]["power"]
        # Monotonic two-segment curve: idle..avg up to 60% load, avg..load above.
        if cpu <= 60:
            p = transform_range(cpu, (0, 60), (pmin, pavg))
        else:
            p = transform_range(cpu, (60, 100), (pavg, pmax))
        return p, v, (p / v if v else 0)

    def estimate_error(self, power: float) -> float:
        """± watts band for an estimate, from the idle..load spread."""
        spread = self.benchmarks["load"]["power"] - self.benchmarks["idle"]["power"]
        return round(max(spread * 0.2, power * 0.15), 2)

    # --- one reading, best source --------------------------------------------

    def measure(self) -> Reading:
        # 1. INA219 — exact, instant.
        if self.ina is not None:
            try:
                v, i, p = self.ina.read()
                if p:
                    return Reading(p, v, i, "ina219")
            except Exception as exc:  # noqa: BLE001 - hardware optional
                print(f"INA219 read failed: {exc}")

        # 2. Raspberry Pi PMIC — measured whole-board power (Pi 5), no hardware.
        if self.pmic:
            p = rpi.pmic_power()
            if p:
                return Reading(p, 0.0, 0.0, "pmic")

        # 3. Battery discharge — measured device input (whole device).
        if self.has_battery:
            p, v, i = self.get_battery_output()
            if p:
                return Reading(p, v, i, "battery")

        # 4. powerstat — measured (x86, privileged) system-power fallback.
        # (RAPL is CPU-package only, so it's a component — see powerguess.cpu —
        #  not a whole-device total source.)
        if self.use_powerstat and not self.prefer_battery:
            p = self._powerstat_once()
            if p:
                v = self.benchmarks["avg"].get("voltage") or 0
                pb, _, _ = self.get_battery_consumption()
                p += pb
                return Reading(p, v, (p / v if v else 0), "powerstat")

        # 4. Estimate.
        p, v, i = self.estimate()
        pb, _, _ = self.get_battery_consumption()
        p += pb
        return Reading(p, v, (p / v if v else i), "estimate", self.estimate_error(p))

    @staticmethod
    def _window(iterable, n=2):
        args = [islice(iterable, i, None) for i in range(n)]
        return zip(*args)

    def _powerstat_once(self) -> Optional[float]:
        """Read a single wattage from powerstat, smoothed if requested."""
        try:
            child = pexpect.spawn("sudo powerstat -R 1", timeout=10)
            child.expect("Watts\r\n")
            watts = None
            for _ in range(5):
                line = [c for c in child.readline().decode("utf-8").strip().split(" ")
                        if c.strip()]
                if len(line) != 13 or line[0] == "--------":
                    break
                try:
                    watts = float(line[-1])
                except ValueError:
                    break
                self.readings.append(watts)
                if self.smooth:
                    avg = [mean(w) for w in self._window(self.readings, 3)]
                    if avg:
                        watts = avg[-1]
            child.terminate(True)
            self.readings = self.readings[-10:]
            return watts
        except Exception as exc:  # noqa: BLE001 - powerstat optional
            print(f"powerstat read failed: {exc}")
            return None

    # --- energy (persisted) + bounds + run loop -------------------------------

    def _load_energy(self) -> float:
        if self.energy_file and os.path.isfile(self.energy_file):
            try:
                with open(self.energy_file) as f:
                    return float(json.load(f).get("energy_wh", 0.0))
            except (OSError, ValueError, KeyError):
                pass
        return 0.0

    def _save_energy(self) -> None:
        if not self.energy_file:
            return
        try:
            with open(self.energy_file, "w") as f:
                json.dump({"energy_wh": round(self.energy_wh, 4)}, f)
        except OSError:
            pass

    def _integrate_energy(self, reading: Reading, now: float) -> None:
        if self._last_ts is not None:
            self.energy_wh += reading.power * ((now - self._last_ts) / 3600)
        self._last_ts = now
        self._energy_dirty += 1
        if self._energy_dirty >= 12:  # persist roughly every minute at 5s cadence
            self._save_energy()
            self._energy_dirty = 0

    def bounds(self) -> tuple:
        """Current (floor, ceiling) watts — the envelope the estimate sits in."""
        return self.benchmarks["idle"]["power"], self.benchmarks["load"]["power"]

    def run(self) -> None:
        self.running = True
        while self.running:
            reading = self.measure()
            if not reading.power and reading.measured:
                # a measured 0 W is meaningless; skip
                threading.Event().wait(self.time_between_measures)
                continue
            self._integrate_energy(reading, time.time())
            if self.auto is not None:
                self.auto.update(reading)
                if self.calibration is None:
                    cal = self.auto.calibration()
                    if cal:
                        self.benchmarks = cal.benchmarks()
            self.current = reading
            for cb in self.callbacks:
                try:
                    cb(reading)
                except Exception as exc:  # noqa: BLE001
                    print(f"callback {cb} failed: {exc}")
            threading.Event().wait(self.time_between_measures)

    def stop(self) -> None:
        self.running = False
        self._save_energy()


if __name__ == "__main__":
    def show(reading: Reading):
        tag = reading.source if reading.measured else f"estimate ±{reading.error_margin}W"
        print(f"{reading.power:6.2f} W  {reading.current:5.2f} A  "
              f"{reading.voltage:5.2f} V  [{tag}]")

    monitor = PowerStatMonitor()
    monitor.add_callback(show)
    monitor.start()
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        monitor.stop()
