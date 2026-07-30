# Calibration

The bundled per-model profiles are coarse. A NUC and a gaming PC both fall
under `pc_generic`, yet they draw very different power. A `Calibration` pins
the estimate to your device with two numbers: idle (the floor) and peak (the
ceiling) watts. Anything you provide beats the generic curve. See
[theory](theory.md) for why those two bounds are all the estimate needs.

## Provenance

Every `Reading` carries its `source` and, for estimates, an `error_margin`.

| source | meaning | error_margin |
| --- | --- | --- |
| `ina219` / `pmic` / `battery` / `powerstat` | measured | 0 |
| `estimate` | modelled from CPU load | ± watts (from the envelope width) |

Prefer a measured source whenever one is available.

## Manual

```python
from powerguess import PowerStatMonitor, Calibration

cal = Calibration(idle_power=2.7, load_power=6.4, voltage=5.0)
monitor = PowerStatMonitor(calibration=cal)
```

Persist or load it as JSON with `cal.save(path)` / `Calibration.load(path)`,
or build it from environment variables with `Calibration.from_env()`
(`CALIBRATION_IDLE_W` / `CALIBRATION_LOAD_W` / `CALIBRATION_VOLTAGE`).

### Idle + PSU rating (no load test)

If you know idle draw and the PSU rating but cannot run a load test, that is
still a valid, if loose, envelope: idle floor, PSU ceiling.

```python
cal = Calibration.from_psu(idle_power=2.7, psu_watts=15)
```

The estimate stays conservative and its error band wide until a real peak is
measured.

## Auto-calibration

`AutoCalibrator` watches the lowest and highest measured power it is fed, using
percentiles to resist outliers, and yields an `auto` calibration. A device
that has a meter for part of its life teaches itself an accurate curve.

```python
from powerguess import AutoCalibrator
auto = AutoCalibrator(path="calibration.json")     # persists when it learns
monitor = PowerStatMonitor(auto_calibrator=auto)   # refines as measured readings arrive
```

A manual calibration always wins over the learned one.

## Measured sources

A real meter removes the guess entirely.

- **INA219** (`pip install powerguess[ina219]`): an I²C power monitor, ideal
  for a headless Pi or SBC.
- **Pi PMIC** (`powerguess.pmic`): Raspberry Pi 5 whole-board power, no
  hardware needed.
- **battery**: laptop discharge rails.

## Trained model

Beyond the two-point curve, a `LinearPredictor` (see [dataset.md](dataset.md))
predicts power from CPU load, frequency, temperature, and core count.

Guided calibration with a smart plug or laptop battery is provided by the
**linux2mqtt** bridge (`linux2mqtt calibrate`), which builds on this library.

---
[← Theory](theory.md) · [Home](../README.md) · [Dataset & model →](dataset.md)
