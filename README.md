# PowerGuess

PowerGuess estimates or measures the power draw of a Linux device. It is a pure
Python library with no I/O bridge. It computes watts and reports where each
number came from. The Home Assistant / MQTT bridge and system telemetry live in
the companion **[linux2mqtt](https://github.com/TigreGotico/linux2mqtt)**
project, which builds on this library.

## Install

```bash
pip install powerguess              # core (psutil, pexpect)
pip install powerguess[ina219]      # + INA219 I²C power-monitor support
```

## What it does

`PowerStatMonitor` picks the best available **whole-device** power source and
labels every reading with its provenance. A guess is never mistaken for a
measurement.

| Source | When | Accuracy |
| --- | --- | --- |
| INA219 (I²C) | a power-monitor HAT is wired | measured |
| Pi PMIC (`vcgencmd`) | Raspberry Pi 5, whole-board, no hardware | measured |
| Battery rails (`/sys`) | devices on battery | measured |
| `powerstat` | x86 fallback | measured |
| CPU-load estimate | everything else | estimated, with an error band |

The estimate sits inside a bounded envelope: an idle floor and a peak/PSU
ceiling. A per-device calibration pins it to your hardware. See
[docs/theory.md](docs/theory.md).

## Use

```python
from powerguess import PowerStatMonitor

monitor = PowerStatMonitor()
reading = monitor.measure()
tag = reading.source if reading.measured else f"estimate ±{reading.error_margin}W"
print(f"{reading.power:.1f} W  [{tag}]")
print("envelope:", monitor.bounds())   # (idle floor, peak ceiling)
```

Calibrate it (manual, learned, or PSU-bounded):

```python
from powerguess import PowerStatMonitor, Calibration

cal = Calibration(idle_power=2.7, load_power=6.4)        # or Calibration.from_psu(...)
monitor = PowerStatMonitor(calibration=cal)
```

## Docs

- [Theory](docs/theory.md): the bounded-estimate model.
- [Calibration](docs/calibration.md): pin the estimate to a device.
- [Dataset & model](docs/dataset.md): collect `features → measured watts`
  (`dataset.py`) and fit a predictor (`train.py`).

## Related projects

- **[linux2mqtt](https://github.com/TigreGotico/linux2mqtt)**: publishes the
  telemetry this library computes to Home Assistant over MQTT.

## License

Apache-2.0
