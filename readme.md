# PowerGuess
 
guess live power usage of linux devices

![Peek 2023-11-11 02-49](https://github.com/OpenJarbas/powerguess/assets/33701864/ea76cf33-8c6a-4de7-bc51-e38a9a6359e6)


submit reference benchmark readings.json to [powerguess/models](./powerguess/models)

in x86 add `powerstat` and `dmidecode` to sudoers in order to not ask password

```
# ALL ALL=NOPASSWD: /usr/bin/powerstat
# ALL ALL=NOPASSWD: /usr/bin/dmidecode
```

# Energy Monitoring

get readings

```python
from ovos_utils import wait_for_exit_signal

from powerguess import PowerStatMonitor


def c(reading, model):
    p, v, i = reading
    print(f"new {model} reading:", p, "W - ", i, "A - ", v, "V")


p = PowerStatMonitor()
p.add_callback(c)

p.start()

wait_for_exit_signal()

p.stop()


```

# Sensors

integrates with [ovos-PHAL-sensors](https://github.com/OpenVoiceOS/ovos-PHAL-sensors)


Battery Sensors
```
BatterySensor
BatteryChargeSensor
BatteryCurrentSensor
BatteryStoredEnergySensor
BatteryPowerConsumptionSensor
BatteryPowerProductionSensor
BatteryStatusSensor
BatteryVoltageSensor
BatteryChargingSensor
```

Power Sensors
```
PowerGuessPowerSensor
PowerGuessCurrentSensor
PowerGuessVoltageSensor
```
