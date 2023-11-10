import dataclasses

from ovos_PHAL_sensors.sensors.base import PercentageSensor, NumericSensor, Sensor, BooleanSensor

from powerguess.guess import PowerStatMonitor
from powerguess.utils import get_battery_info, get_energy_delta_per_second


@dataclasses.dataclass
class PowerGuessPowerSensor(NumericSensor):
    unique_id: str = "power"
    device_name: str = "powerguess"
    unit: str = "W"

    @property
    def value(self):
        p, v, i = PowerStatMonitor.current_value
        return p

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "power",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class PowerGuessCurrentSensor(NumericSensor):
    unique_id: str = "current"
    device_name: str = "powerguess"
    unit: str = "A"

    @property
    def value(self):
        p, v, i = PowerStatMonitor.current_value
        return i

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "current",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class PowerGuessVoltageSensor(NumericSensor):
    unique_id: str = "voltage"
    device_name: str = "powerguess"
    unit: str = "V"

    @property
    def value(self):
        p, v, i = PowerStatMonitor.current_value
        return v

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "voltage",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatterySensor(PercentageSensor):
    unique_id: str = "percent"
    device_name: str = "battery"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        return round(battery["capacity"], 3)

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "battery",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryPowerConsumptionSensor(NumericSensor):
    unique_id: str = "power_consumption"
    device_name: str = "battery"
    unit: str = "W"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        if battery["status"] == "Charging":
            return round(battery["power"], 3)
        return 0

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "power",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryPowerProductionSensor(NumericSensor):
    unique_id: str = "power_production"
    device_name: str = "battery"
    unit: str = "W"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        if battery["status"] == "Discharging":
            return round(battery["power"], 3)
        return 0

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "power",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryCurrentSensor(NumericSensor):
    """ negative if battery is discharging"""
    unique_id: str = "current"
    device_name: str = "battery"
    unit: str = "A"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        c = round(battery["current"], 3)
        if battery["status"] == "Discharging":
            return c * -1
        return c

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "current",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryVoltageSensor(NumericSensor):
    unique_id: str = "voltage"
    device_name: str = "battery"
    unit: str = "V"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        return round(battery["voltage"], 3)

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "voltage",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryChargeSensor(NumericSensor):
    unique_id: str = "charge"
    device_name: str = "battery"
    unit: str = "Ah"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        return round(battery["charge"], 3)

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryEnergyDeltaSensor(NumericSensor):
    unique_id: str = "energy_delta"
    device_name: str = "battery"
    unit: str = "mWh/s"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        return get_energy_delta_per_second(self.unit.replace("/s", ""))[0]

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryStatusSensor(Sensor):
    unique_id: str = "status"
    device_name: str = "battery"
    unit: str = ""

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return "unknown"
        return battery["status"]

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "battery"}


@dataclasses.dataclass
class BatteryStoredEnergySensor(NumericSensor):
    unique_id: str = "stored_energy"
    device_name: str = "battery"
    unit: str = "kWh"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return 0
        return round(battery["charge"] * battery["voltage"], 5)

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "energy_storage",
                "unit_of_measurement": self.unit}


@dataclasses.dataclass
class BatteryChargingSensor(BooleanSensor):
    unique_id: str = "charging"
    device_name: str = "battery"

    @property
    def value(self):
        battery = list(get_battery_info())[0]
        if battery is None:
            return False
        return battery["status"] == "Charging"

    @property
    def attrs(self):
        return {"friendly_name": self.__class__.__name__,
                "device_class": "battery_charging",
                "unit_of_measurement": self.unit}


if __name__ == "__main__":
    print(BatterySensor().value, "%")
    print(BatteryPowerConsumptionSensor().value, "W")
    print(BatteryPowerProductionSensor().value, "W")
    print(BatteryCurrentSensor().value, "A")
    print(BatteryVoltageSensor().value, "V")
    print(BatteryChargeSensor().value, "Ah")
    print(BatteryStoredEnergySensor().value, "kWh")
    print(BatteryStatusSensor().value)
    print(BatteryEnergyDeltaSensor().value, "mWh/s")
    # 79 %
    # 9.128 W
    # 0.54 A
    # 16.904 V
    # 3.492 Ah
    # 59.029 kWh
    # Charging
