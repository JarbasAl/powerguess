# Raspberry Pi / SBC

Single-board computers are the case PowerGuess exists for — headless, no battery,
no smart plug, and no x86 power telemetry. Here's how it behaves and how to get
real numbers.

## What works out of the box

- **Model detection** — `/proc/device-tree/model` identifies the board and loads
  the matching profile (`pi4.json`, `pi3b.json`, `pi02.json`, …).
- **CPU component** — utilization, frequency, and temperature (from
  `/sys/class/thermal`) are published like on any host. (No `cpu_power`: RAPL is
  x86-only.)
- **Total power** — with no measured source, it's the **estimate** from CPU load
  against the board profile, with an honest error band.

## Get measured power (best → easiest)

1. **Raspberry Pi 5 only — zero hardware.** The Pi 5 PMIC reports per-rail voltage
   and current via `vcgencmd pmic_read_adc`; PowerGuess sums them into real
   whole-board power (source `pmic`). Auto-detected — the SBC analogue to x86 RAPL.
   **Pi 3/4 have a PMIC but expose no ADC telemetry**, so there's no firmware-only
   power path there — PowerGuess probes once at startup and, finding none, won't
   poll it.
2. **INA219 / INA260 power HAT — any Pi/SBC, including Pi 3/4.** A cheap I²C power
   monitor on the supply gives exact total power. `pip install powerguess[ina219]`,
   `USE_INA219=true`. This is the measured path for Pi 3/4 and non-Pi SBCs.
3. **Calibrate the estimate with a smart plug** — `powerguess-calibrate` measures
   idle and peak over MQTT and pins the profile to your board + peripherals. Or
   bound it with `CALIBRATION_IDLE_W` + `CALIBRATION_PSU_W`.

The profiles are deliberately coarse (a Pi 4 with a couple of USB SSDs draws very
differently from a bare one), so a meter or a calibration is the way to trust the
number — and that data can feed the [dataset/model](dataset.md).

## Undervoltage & throttling

On a Pi, `vcgencmd get_throttled` is exposed as Home Assistant **binary sensors**
(`device_class: problem`): `undervoltage`, `throttled`, and
`undervoltage_occurred`. Undervoltage on a Pi causes SD-card corruption and silent
slowdowns, so this is worth an alert regardless of the power number. Auto-enabled
when `vcgencmd` is present (`USE_RPI`).

## Summary

| | Pi 3/4 (bare) | Pi 5 (bare) | + INA219 HAT | + smart plug |
| --- | --- | --- | --- | --- |
| total power | estimate (±band) | **measured (PMIC)** | **measured** | calibrated estimate |
| CPU util/temp/freq | ✅ | ✅ | ✅ | ✅ |
| undervoltage/throttle | ✅ | ✅ | ✅ | ✅ |

So: a **Pi 5** gets real power for free; a **Pi 3/4** needs an INA219 HAT or a
smart-plug calibration for measured power, but still gets the estimate, CPU
telemetry, and undervoltage/throttling sensors.
