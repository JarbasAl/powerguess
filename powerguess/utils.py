import os
import subprocess
import time


def transform_range(value: float, r1: tuple, r2: tuple):
    """ scale N from range (x, y) to (X, Y) """
    scale = (r2[1] - r2[0]) / (r1[1] - r1[0])
    return (value - r1[0]) * scale


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


def get_product_name():
    try:
        # ALL ALL=NOPASSWD: /usr/bin/dmidecode
        p = subprocess.check_output("sudo dmidecode | grep -A3 '^System Information'", shell=True).decode("utf-8")
        return p.split("Product Name: ")[-1].split("\n")[0]
    except:
        return ""


def get_energy_delta_per_second(unit="mWh"):
    bat = list(get_battery_info())[0]
    t = 1
    time.sleep(t)
    bat2 = list(get_battery_info())[0]
    delta = bat2["charge"] - bat["charge"]
    current = delta * t
    p = bat2["voltage"] * current
    e = p * (t / 3600)
    if unit == "mWh":
        e = e * 1000
    elif unit == "kWh":
        e = e / 1000
    else:
        unit = "Wh"
    unit += "/s"
    return e, unit
