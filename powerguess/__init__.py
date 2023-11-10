import json
import os
import platform
import subprocess
import threading
from distutils.spawn import find_executable
from itertools import islice
from statistics import mean

import pexpect
import psutil


def get_battery_info():
    # https://www.kernel.org/doc/html/latest/power/power_supply_class.html
    for b in os.listdir("/sys/class/power_supply/"):
        with open(f"/sys/class/power_supply/{b}/uevent") as f:
            data = f.read()
        voltage = 0
        is_battery = False
        current = 0
        power = 0
        charge = 0
        charge_full = 0
        cap = 0
        status = ""
        name = b
        for l in data.split("\n"):
            try:
                k, v = l.split("=")
            except:
                continue
            # µV, µA, µAh, µWh
            if k == "POWER_SUPPLY_TYPE" and v == "Battery":
                is_battery = True
            if k == "POWER_SUPPLY_VOLTAGE_NOW":
                voltage = int(v) / 1000000  # µV
            if k == "POWER_SUPPLY_CURRENT_NOW":
                current = int(v) / 1000000  # µA
            if k == "POWER_SUPPLY_POWER_NOW":
                power = int(v) / 1000000  # µW
            if k == "POWER_SUPPLY_CHARGE_NOW":
                charge = int(v) / 1000000  # µAh
            if k == "POWER_SUPPLY_CHARGE_FULL":
                charge_full = int(v) / 1000000  # µAh
            if k == "POWER_SUPPLY_CAPACITY":
                cap = int(v)  # %
            if k == "POWER_SUPPLY_STATUS":
                status = v
            if k == "POWER_SUPPLY_NAME":
                name = v

        if is_battery:
            power = power or voltage * current
            yield {
                "capacity": cap,
                "voltage": voltage,
                "current": current,
                "power": power,
                "charge": charge,
                "status": status,
                "name": name,
                "time_left": (1 / ((charge_full - charge) / current))
                if current and charge_full - charge else -1
            }


def get_model():
    p = ""
    if os.path.isfile("/proc/device-tree/model"):
        p = "/proc/device-tree/model"
    elif os.path.isfile("/sys/firmware/devicetree/base/model"):
        p = "/sys/firmware/devicetree/base/model"
    if p:
        with open(p) as f:
            model = f.read()
        return model
    return get_product_name()


def get_power_supply_info():
    p, v, i = PowerStatMonitor.current_value

    print("# name:", PowerStatMonitor.model)
    print("voltage:", v, "V")
    print("current:", i, "A")
    print("power:", p, "W")
    return p, v, i


def get_product_name():
    try:
        # ALL ALL=NOPASSWD: /usr/bin/dmidecode
        p = subprocess.check_output("sudo dmidecode | grep -A3 '^System Information'", shell=True).decode("utf-8")
        return p.split("Product Name: ")[-1].split("\n")[0]
    except:
        return ""


class PowerStatMonitor(threading.Thread):
    running = False
    current_value = 0, 0, 0  # (p, v, i)
    ignore_battery = False
    model = get_model()
    benchmarks = {}
    callbacks = []

    def __init__(self, smooth=False, time_between_measures=5):
        super().__init__(daemon=True)
        self.smooth = smooth
        self.time_between_measures = time_between_measures
        self.readings = []

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

        PowerStatMonitor.current_value = cls.guesstimate_cpu()

    @classmethod
    def add_callback(cls, cb):
        PowerStatMonitor.callbacks.append(cb)

    def run(self) -> None:
        PowerStatMonitor.running = True
        while PowerStatMonitor.running:
            for reading in self.measure_powerstat(self.smooth):
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
    def guesstimate_cpu(cls):
        p, v, i = 0, 0, 0

        if PowerStatMonitor.ignore_battery:
            bat = None
        else:
            bat = list(get_battery_info())

        if bat:  # estimate from battery readings
            bat = bat[0]
            if bat["status"] == "Discharging":
                # assume the energy is being consumed by the laptop
                p = bat["power"]
                v = bat["voltage"]
                i = bat["current"]
                return p, v, i

        cpu = psutil.cpu_percent()

        pmax = cls.benchmarks["load"]["power"]
        pmin = cls.benchmarks["idle"]["power"]
        pavg = cls.benchmarks["avg"]["power"]
        imax = cls.benchmarks["load"].get("current") or 0
        iavg = cls.benchmarks["avg"].get("current") or imax * 0.6
        imin = cls.benchmarks["idle"].get("current") or imax * 0.3
        vmax = cls.benchmarks["load"].get("voltage") or 0
        vavg = cls.benchmarks["avg"].get("voltage") or vmax
        vmin = cls.benchmarks["idle"].get("voltage") or vmax

        # assume max consumption if cpu >= 80%
        if cpu >= 80:
            p = pmax
            i = imax
            v = vmax
        # assume idle consumption if cpu <= 10%
        elif cpu <= 10:
            p = pmin
            i = imin
            v = vmin
        # assume 100% == avg consumption if 10 < cpu < 50
        elif 10 < cpu < 60:
            p = cpu * pavg / 100
            i = cpu * iavg / 100
            v = vavg
        # assume 100% == under stress consumption if 50 < cpu < 80
        else:
            p = cpu * pmax / 100
            i = cpu * imax / 100
            v = vavg

        if pmin:
            p = max(p, pmin)
            i = max(i, imin)
        if pmax:
            p = min(p, pmax)
            i = min(i, imax)

        if i and not v:
            v = p / i  # V
        if v and not i:
            i = p / v  # A

        return p, v, i

    def measure_powerstat(self, smooth=False):
        # ALL ALL=NOPASSWD: /usr/bin/powerstat
        p, v, i = self.guesstimate_cpu()
        if find_executable("powerstat"):
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
                    i = p / v
                    yield p, v, i
                    if len(self.readings) > 10:
                        self.readings = self.readings[-10:]
                child.terminate(True)
            except Exception as e:
                print(e)
        else:
            yield p, v, i


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
