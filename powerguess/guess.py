import json
import os
import platform
import threading
from distutils.spawn import find_executable
from itertools import islice
from statistics import mean

import pexpect
import psutil

from powerguess.utils import get_battery_info, get_model, transform_range


class PowerStatMonitor(threading.Thread):
    running = False
    current_value = 0, 0, 0  # (p, v, i)
    prefer_battery = False
    disable_powerstat = find_executable("powerstat")
    model = get_model()
    benchmarks = {}
    callbacks = []

    def __init__(self, smooth=False, time_between_measures=5):
        super().__init__(daemon=True)
        self.smooth = smooth
        self.time_between_measures = time_between_measures
        self.readings = []
        self.has_battery = bool(self.get_battery())
        if self.model:
            self.set_model(self.model)

    @classmethod
    def set_model(cls, model):
        cls.model = model
        if "Raspberry Pi 4" in cls.model:
            m = "pi4.json"
        elif "Raspberry Pi 3 Model B Plus" in cls.model:
            m = "pi3b+.json"
        elif "Raspberry Pi 3" in cls.model:
            m = "pi3b.json"
        elif "Raspberry Pi 2" in cls.model:
            m = "pi2.json"
        elif "Raspberry Pi Zero" in cls.model:
            m = "pi0.json"
        elif "U500-H" in model:
            m = "minipc_generic.json"
        # catch all - generic laptop
        elif platform.machine() == "x86_64" and list(get_battery_info()):
            m = "laptop_generic.json"
        # catch all - sbc
        elif platform.machine() == "aarch64" or "Raspberry Pi" in model:
            m = "sbc_generic.json"
        # catch all - PC
        else:
            m = "pc_generic.json"

        with open(f"{os.path.dirname(__file__)}/models/{m}") as f:
            PowerStatMonitor.benchmarks = json.load(f)

        PowerStatMonitor.current_value = cls.guesstimate()

    @classmethod
    def add_callback(cls, cb):
        PowerStatMonitor.callbacks.append(cb)

    @property
    def battery(self):
        if self.has_battery:
            return self.get_battery()
        return {}

    @classmethod
    def get_battery_consumption(cls):
        # energy being consumed in addition to energy from laptop
        bat = cls.get_battery()
        if bat:
            if bat["status"] == "Charging":
                p = bat["power"]
                v = bat["voltage"]
                i = bat["current"]
                return p, v, i
        return 0, 0, 0

    @classmethod
    def get_battery_output(cls):
        # energy being provided to laptop
        bat = cls.get_battery()
        if bat:
            if bat["status"] == "Discharging":
                p = bat["power"]
                v = bat["voltage"]
                i = bat["current"]
                return p, v, i
        return 0, 0, 0

    def run(self) -> None:
        PowerStatMonitor.running = True
        while PowerStatMonitor.running:
            for reading in self.measure_powerstat(self.smooth):
                if not reading[0]:
                    continue  # 0 power consumption is impossible
                PowerStatMonitor.current_value = reading
                for cb in self.callbacks:
                    try:
                        cb(reading, self.model)
                    except Exception as e:
                        print(f"callback {cb} failed: {e}")
                        continue
            threading.Event().wait(self.time_between_measures)

    def stop(self):
        PowerStatMonitor.running = False

    @staticmethod
    def _window(iterable, n=2):
        # window('123', 2) --> '12' '23'
        args = [islice(iterable, i, None) for i in range(n)]
        return zip(*args)

    @classmethod
    def get_battery(cls):
        bat = list(get_battery_info())
        if bat:  # estimate from battery readings
            bat = bat[0]
        return bat or None

    @classmethod
    def guesstimate(cls):

        # assume battery output == total laptop input
        p, v, i = cls.get_battery_output()
        if p:
            return p, v, i

        # estimate consumption based on cpu usage
        cpu = psutil.cpu_percent()

        pmax = cls.benchmarks["load"]["power"]
        pmin = cls.benchmarks["idle"]["power"]
        pavg = cls.benchmarks["avg"]["power"]
        imax = cls.benchmarks["load"].get("current") or 0
        iavg = cls.benchmarks["avg"].get("current") or imax * 0.6
        imin = cls.benchmarks["idle"].get("current") or imax * 0.3
        i, v, p = 0, 0, 0

        if cpu < 60:
            p = transform_range(cpu, (0, 100), (pmin, pavg))
            if imin and iavg:
                i = transform_range(cpu, (0, 100), (imin, iavg))
            else:
                v = cls.benchmarks["avg"].get("voltage") or \
                    cls.benchmarks["load"].get("voltage") or \
                    cls.benchmarks["idle"].get("voltage") or 0
        else:
            p = transform_range(cpu, (0, 100), (pmin, pmax))
            if imin and imax:
                i = transform_range(cpu, (0, 100), (imin, imax))
            else:
                v = cls.benchmarks["load"].get("voltage") or \
                    cls.benchmarks["avg"].get("voltage") or \
                    cls.benchmarks["idle"].get("voltage") or 0

        if i and not v:
            v = p / i  # V
        if v and not i:
            i = p / v  # A

        return p, v, i

    def measure_powerstat(self, smooth=False):
        if self.prefer_battery and self.has_battery:
            # assume battery output == total laptop input
            p, v, i = self.get_battery_output()
            if p:
                yield p, v, i
                return

        # consumption from cpu
        p, v, i = self.guesstimate()

        # consumption from charging
        pb, vb, ib = self.get_battery_consumption()

        # consumption from powerstat
        # ALL ALL=NOPASSWD: /usr/bin/powerstat
        if not self.disable_powerstat and find_executable("powerstat"):
            try:
                child = pexpect.spawn('sudo powerstat -R 1')
                child.expect('  Time    User  Nice   Sys  Idle    IO  Run Ctxt/s  IRQ/s Fork Exec Exit  Watts\r\n')
                while True:
                    l = [_ for _ in child.readline(1).decode("utf-8").strip().split(" ") if _.strip()]
                    if len(l) != 13 or l[0] == '--------':
                        break
                    try:
                        p = float(l[-1])
                    except:
                        break
                    self.readings.append(p)
                    if smooth:
                        avg = [mean(w) for w in self._window(self.readings, 3)]
                        if avg:
                            p = avg[-1]
                    p += pb
                    i = p / v
                    yield p, v, i
                    if len(self.readings) > 10:
                        self.readings = self.readings[-10:]
                child.terminate(True)
            except Exception as e:
                print(e)
        else:
            yield p + pb, v, i + ib


if __name__ == "__main__":
    # in x86 add to sudoers
    # ALL ALL=NOPASSWD: /usr/bin/powerstat
    # ALL ALL=NOPASSWD: /usr/bin/dmidecode

    def c(reading, model):
        p, v, i = reading
        print(f"new {model} reading:", p, "W - ", i, "A - ", v, "V")


    # do this at PHAL plugin init time
    p = PowerStatMonitor()
    p.add_callback(c)
    p.start()

    from ovos_utils import wait_for_exit_signal

    wait_for_exit_signal()

    p.stop()
