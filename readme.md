# PowerGuess
 
guess live power usage of linux devices

in x86 add `powerstat` and `dmidecode` to sudoers in order to not ask password

```
# ALL ALL=NOPASSWD: /usr/bin/powerstat
# ALL ALL=NOPASSWD: /usr/bin/dmidecode
```

get readings

```python
from powerguess import PowerStatMonitor, get_power_supply_info
import time

# do this at PHAL plugin init time
p = PowerStatMonitor()
p.start()  # gather readings in background

time.sleep(5)
get_power_supply_info()
time.sleep(1)
get_power_supply_info()
time.sleep(1)
get_power_supply_info()
time.sleep(1)
get_power_supply_info()
time.sleep(1)
get_power_supply_info()

p.stop()

```