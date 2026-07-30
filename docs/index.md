# PowerGuess documentation

PowerGuess is a pure-Python library that estimates or measures the power draw
of a Linux device, with provenance on every reading. The MQTT / Home Assistant
bridge and system telemetry live in the companion **linux2mqtt** project.

## Pages

- **[Theory](theory.md)**: the bounded-estimate model. Power lives between an
  idle floor and a PSU ceiling. The estimate interpolates within it.
- **[Calibration](calibration.md)**: pin the estimate to your device with
  manual idle/peak values, idle plus PSU rating, or the `AutoCalibrator`,
  which learns from measured readings.
- **[Dataset & model](dataset.md)**: collect `features → measured watts` with
  `dataset.py` and fit a predictor with `train.py`.

## API

- `PowerStatMonitor`: `measure() -> Reading`, `bounds() -> (floor, ceiling)`,
  energy accounting, callbacks.
- `Reading`: `power`, `voltage`, `current`, `source`, `measured`, `error_margin`.
- `Calibration` / `AutoCalibrator`: per-device idle/peak, manual or learned.
- Measured sources: `powerguess.ina219`, `powerguess.pmic`, battery (`utils`),
  powerstat.
- `powerguess.model` + `train.py`: a pluggable `LinearPredictor` over device
  features.
