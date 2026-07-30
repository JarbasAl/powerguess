# Power dataset

PowerGuess's estimate is only as good as its idle/load profile. The path to a
better estimate is data: pair device features with measured watts from
devices that have a real meter, then fit a model. `dataset.py` is the
collector.

## What it collects

On any device with a measured source (INA219, powerstat/RAPL, or a
discharging battery), each sample is one JSONL row.

```json
{"ts": "2026-06-04T15:00:00", "arch": "aarch64", "model": "Raspberry Pi 4 Model B",
 "cpu_percent": 37.0, "cpu_freq_mhz": 1500.0, "n_cores": 4.0, "has_battery": 0.0,
 "source": "ina219", "watts": 4.12}
```

Estimated readings are never written. Only ground truth goes in, so the
dataset cannot be poisoned by the model it trains.

## Collect

```bash
python dataset.py --out powerguess.jsonl --samples 500 --interval 5
```

Or let the running bridge collect continuously by setting `DATASET_FILE`.

```bash
DATASET_FILE=/data/powerguess.jsonl python -m powerguess
```

Devices with no meter produce nothing. That is expected.

## ML task

The task is a regression: features to watts, one model per architecture,
because x86 RAPL behaves differently from ARM SBCs. The features are defined
once in `powerguess.model.FEATURES` and shared by the collector and the
predictor, so a trained model drops straight in.

Fit one with the bundled trainer (ordinary least squares, pure Python, no ML
dependency).

```bash
python train.py --data powerguess.jsonl --out model.json
python train.py --data powerguess.jsonl --arch aarch64 --out pi.json   # per arch
```

It writes a small JSON file of linear coefficients.

```json
{"intercept": 1.8, "coefficients": {"cpu_percent": 0.045, "n_cores": 0.6, ...}}
```

Point the bridge at it with `MODEL_FILE=model.json`. Readings then come from
the model instead of the idle/load curve. The features
(`powerguess.model.FEATURES`) include CPU load, frequency, core count, load
average, and temperature. Richer model families can be added behind the same
`predict(features) -> watts` interface in `powerguess.model`.

## Publishing

The aggregated corpus is intended for the Hugging Face Hub, for device-power
regression. Contributors with smart plugs or INA219 HATs can extend coverage
across architectures and peripherals. The more meters, the better every
meter-less device's estimate becomes.

---
[← Calibration](calibration.md) · [Home](../README.md)
