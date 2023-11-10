# PowerGuess
 
guess live power usage of linux devices

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

# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 13.38 W -  0.669 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 11.04 W -  0.5519999999999999 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 27.06 W -  1.353 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 16.37 W -  0.8185 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 17.77 W -  0.8885 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 23.36 W -  1.168 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 23.56 W -  1.178 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 12.78 W -  0.639 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 23.54 W -  1.177 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 36.33 W -  1.8165 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 25.59 W -  1.2795 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 41.92 W -  2.096 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 17.58 W -  0.8789999999999999 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 17.01 W -  0.8505 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 21.15 W -  1.0574999999999999 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 19.28 W -  0.9640000000000001 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 11.2 W -  0.5599999999999999 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 7.39 W -  0.3695 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 10.1 W -  0.505 A -  20 V
# new ASUS TUF Gaming F15 FX506HM_FX506HM reading: 15.18 W -  0.759 A -  20 V

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
BatteryPowerSensor
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