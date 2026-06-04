# PowerGuess documentation

A pure-Python library that estimates or measures the power draw of a Linux device,
with provenance on every reading. The MQTT / Home Assistant bridge and system
telemetry are in the companion **linux2mqtt** project.

## Pages

- **[Theory](theory.md)** — the bounded-estimate model: power lives between an
  idle floor and a PSU ceiling; the estimate interpolates within it.
- **[Calibration](calibration.md)** — pin the estimate to your device: manual
  idle/peak, idle + PSU rating, or the `AutoCalibrator` that learns from measured
  readings.
- **[Dataset & model](dataset.md)** — collect `features → measured watts` with
  `dataset.py` and fit a predictor with `train.py`.

## API

- `PowerStatMonitor` — `measure() -> Reading`, `bounds() -> (floor, ceiling)`,
  energy accounting, callbacks.
- `Reading` — `power`, `voltage`, `current`, `source`, `measured`, `error_margin`.
- `Calibration` / `AutoCalibrator` — per-device idle/peak, manual or learned.
- measured sources: `powerguess.ina219`, `powerguess.pmic`, battery (`utils`),
  powerstat.
- `powerguess.model` + `train.py` — pluggable `LinearPredictor` over device
  features.
