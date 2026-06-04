import os
import subprocess


def transform_range(value: float, r1: tuple, r2: tuple):
    """Linearly map ``value`` from range ``r1`` (x, y) to range ``r2`` (X, Y)."""
    scale = (r2[1] - r2[0]) / (r1[1] - r1[0])
    return r2[0] + (value - r1[0]) * scale


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
    # Explicit override — useful in containers, where /proc/device-tree and
    # /sys aren't reliably visible, or for unusual boards.
    env = os.getenv("POWERGUESS_MODEL")
    if env:
        return env
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
    # `sudo -n` never prompts: it fails immediately when passwordless dmidecode
    # isn't configured, instead of blocking on a TTY password prompt at startup.
    #   ALL ALL=NOPASSWD: /usr/bin/dmidecode
    try:
        out = subprocess.run(["sudo", "-n", "dmidecode", "-s", "system-product-name"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return out.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return ""
