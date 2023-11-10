from threading import Event

from ovos_PHAL_sensors.device import BaseDevice
from ovos_PHAL_sensors.sensors.base import _norm
from ovos_plugin_manager.templates.phal import PHALPlugin

from powerguess.sensors import PowerStatMonitor, PowerGuessPowerSensor, PowerGuessVoltageSensor, \
    PowerGuessCurrentSensor, BatteryPowerConsumptionSensor, BatteryPowerProductionSensor, BatterySensor, \
    BatteryStatusSensor, BatteryChargingSensor, BatteryEnergyDeltaSensor,\
    BatteryVoltageSensor, BatteryStoredEnergySensor, BatteryChargeSensor, BatteryCurrentSensor


class PowerSupplyDevice(BaseDevice):

    def __init__(self):
        def c(reading, model):
            PowerGuessVoltageSensor().sensor_update()
            PowerGuessCurrentSensor().sensor_update()
            PowerGuessPowerSensor().sensor_update()

        self.power = PowerStatMonitor()
        self.power.add_callback(c)
        self.power.start()

        super().__init__(_norm("PSU " + PowerStatMonitor.model))

    def stop(self):
        if self.power:
            self.power.stop()

    @property
    def sensors(self):
        return [PowerGuessPowerSensor(),
                PowerGuessCurrentSensor(),
                PowerGuessVoltageSensor(),
                BatterySensor(),
                BatteryChargeSensor(),
                BatteryCurrentSensor(),
                BatteryStoredEnergySensor(),
                BatteryChargingSensor(),
                BatteryPowerConsumptionSensor(),
                BatteryPowerProductionSensor(),
                BatteryStatusSensor(),
                BatteryVoltageSensor(),
                BatteryEnergyDeltaSensor()
                ]


class PHALPSU(PHALPlugin):
    def __init__(self, bus, name="phal_psu", config=None):
        self.running = False
        super().__init__(bus, name, config or {})

    def initialize(self):
        self.ha_url = self.config.get("ha_host")
        self.ha_token = self.config.get("ha_token")
        self.name = self.config.get("name", "OVOSDevicePSU")
        PowerSupplyDevice.bind(self.name, self.ha_url, self.ha_token, self.bus,
                               disable_bus=self.config.get("disable_bus", False),
                               disable_ha=self.config.get("disable_ha", True),
                               disable_mqtt=self.config.get("disable_mqtt", False),
                               disable_file_logger=self.config.get("disable_filelog", True),
                               mqtt_config=self.config.get("mqtt_config") or {})
        self.device = PowerSupplyDevice()

    def run(self):
        self.initialize()
        self.running = True
        while self.running:
            Event().wait(10)
            self.device.update()
        self.device.stop()

    def shutdown(self):
        self.device.stop()


def standalone_launch():

    from ovos_utils.messagebus import FakeBus
    from ovos_utils import wait_for_exit_signal
    from ovos_config import Configuration

    conf = Configuration().get("PHAL", {}).get("ovos-PHAL-sensors", {})
    sensor = PHALPSU(bus=FakeBus(), config=conf)
    wait_for_exit_signal()


if __name__ == "__main__":

    standalone_launch()
