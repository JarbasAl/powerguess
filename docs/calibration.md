# Calibration

The generic per-model profiles are coarse — a NUC and a gaming PC both fall under
`pc_generic` yet draw wildly different power. Calibration pins the estimate to
*your* device with two numbers: idle (the floor) and peak (the ceiling) watts.
Anything you provide beats the generic curve. See [theory](theory.md) for why
those two bounds are all the estimate needs.

## The fastest path: the wizard

`powerguess-calibrate` measures both bounds for you using an MQTT smart plug as
the meter — it reads the plug while prompting you to idle the device and then load
it, then writes `calibration.json`:

```bash
powerguess-calibrate
```

It asks for the plug's MQTT topic, the supply voltage, and (optionally) the PSU
rating for a sanity check. If you can't run a load test, it falls back to bounding
by the PSU rating.

## Provenance first

Every reading carries its `source` and, for estimates, an `error_margin`:

| source | meaning | error_margin |
| --- | --- | --- |
| `ina219` | measured by an I²C power monitor | 0 |
| `powerstat` | measured via x86 RAPL | 0 |
| `battery` | measured from battery discharge | 0 |
| `estimate` | modelled from CPU load | ± watts |

In Home Assistant these surface as the **Source** and **Error Margin** sensors,
so a guess is never mistaken for a measurement. Prefer a measured source whenever
one is available.

## Measured: INA219 (recommended for Pi/SBC)

A cheap INA219 I²C power monitor on the device's supply gives a true reading on
exactly the headless boards where estimation is weakest:

```bash
pip install powerguess[ina219]
USE_INA219=true INA219_BUS=1 INA219_ADDRESS=0x40 python -m powerguess
```

## Manual calibration

Measure your device's idle and peak draw once (e.g. with a smart plug) and pass
them in:

```bash
CALIBRATION_IDLE_W=2.7 CALIBRATION_LOAD_W=6.4 python -m powerguess
```

or persist a `calibration.json` and point `CALIBRATION_FILE` at it:

```json
{"idle_power": 2.7, "load_power": 6.4, "voltage": 5.0, "source": "manual"}
```

### Idle + PSU rating (no load test)

If you know the idle draw and the PSU rating but can't run a load test, that's
enough for a valid (if loose) envelope — idle is the floor, the PSU rating the
ceiling (see [theory](theory.md)):

```bash
CALIBRATION_IDLE_W=2.7 CALIBRATION_PSU_W=15 python -m powerguess
```

The estimate is conservative and its error band wide until you measure a real
peak.

## Auto-calibration

With `AUTO_CALIBRATE=true` (the default) and `CALIBRATION_FILE` set, PowerGuess
watches the lowest and highest **measured** power it sees and writes an `auto`
calibration back to that file. A device that has a meter for part of its life —
or runs on battery sometimes — teaches itself an accurate idle/load curve that
the estimate then uses when the meter isn't available.

```bash
CALIBRATION_FILE=/data/calibration.json python -m powerguess
```

A manual calibration always wins over the learned one.

## Best estimate: a trained model

Beyond the two-point curve, point `MODEL_FILE` at a trained linear model (see
[dataset.md](dataset.md)) to predict from CPU load, frequency, and core count.
