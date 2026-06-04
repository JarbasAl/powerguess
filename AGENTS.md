# PowerGuess — agent onboarding

A **pure power library**: estimate or measure the power draw of a Linux device.
No I/O bridge — it computes watts with provenance and nothing else. The MQTT /
Home Assistant bridge and system telemetry (CPU/GPU/Pi temperature, throttling, …)
live in the companion **linux2mqtt** project, which depends on this.

**Org:** TigreGotico / **Branch:** dev (work) / master (stable)

## Layout

| Path | Purpose |
|------|---------|
| `powerguess/reading.py` | `Reading` frozen dataclass — value + provenance (`source`, `error_margin`) |
| `powerguess/guess.py` | `PowerStatMonitor` — whole-device source priority (ina219>pmic>battery>powerstat>estimate), energy, bounds, callbacks |
| `powerguess/calibration.py` | `Calibration` + `AutoCalibrator` (manual/file/env/PSU + percentile-learned idle/peak) |
| `powerguess/ina219.py` | INA219 I²C power meter (`ina219` extra) — measured total |
| `powerguess/pmic.py` | Raspberry Pi 5 PMIC board power via vcgencmd — measured total |
| `powerguess/model.py` | `FEATURES`, `current_features`, `LinearPredictor` (pluggable estimate) |
| `powerguess/utils.py` | `/sys` battery reads, model detection, CPU temp, `transform_range` |
| `powerguess/models/*.json` | per-device idle/avg/load benchmark profiles |
| `dataset.py` / `train.py` | collect `features → measured watts` JSONL, then least-squares fit a model JSON |
| `docs/` | theory, calibration, dataset |
| `test/` | offline pytest suite (battery `/sys`, INA219 SMBus mocked) |

## Boundary (powerguess vs linux2mqtt)

powerguess = **watts only** (whole-device power: estimate + INA219/PMIC/battery/
powerstat + calibration + dataset/model). Anything non-watt — CPU/GPU/Pi
telemetry (util, freq, temperature, throttling, overclock), MQTT/HA discovery,
energy/cost accounting, the calibration wizard — belongs in **linux2mqtt**, which
imports this library for power. RAPL CPU-package power and GPU power ride with
their telemetry in linux2mqtt; PMIC is whole-board, so it stays here.

## Conventions

- **Provenance is load-bearing:** every `Reading` records its `source`; estimates
  carry an `error_margin`. Never emit a guess that looks like a measurement, and
  never feed an estimate into the `AutoCalibrator` or `dataset.py` (ground truth only).
- No OVOS dependency; no `distutils` (use `shutil.which`).
- Per-instance state only on `PowerStatMonitor` (no class-level mutable state).
- Tests are offline; mock `/sys` reads.
- Versions bump from conventional-commit prefixes — never edit `powerguess/version.py`.

## Run

```bash
pip install -e .[test]
pytest -q
```
