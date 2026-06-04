# Power dataset

PowerGuess's estimate is only as good as its idle/load profile. The path to a
better estimate is data: pair **device features** with **measured watts** from
devices that have a real meter, then fit a model. `dataset.py` is the collector.

## What it collects

On any device with a measured source (INA219, powerstat/RAPL, or a discharging
battery), each sample is one JSONL row:

```json
{"ts": "2026-06-04T15:00:00", "arch": "aarch64", "model": "Raspberry Pi 4 Model B",
 "cpu_percent": 37.0, "cpu_freq_mhz": 1500.0, "n_cores": 4.0, "has_battery": 0.0,
 "source": "ina219", "watts": 4.12}
```

Estimated readings are **never** written — only ground truth goes in, so the
dataset can't be poisoned by the very model it trains.

## Collect

```bash
python dataset.py --out powerguess.jsonl --samples 500 --interval 5
```

Or let the running bridge collect continuously by setting `DATASET_FILE`:

```bash
DATASET_FILE=/data/powerguess.jsonl python -m powerguess
```

Devices with no meter produce nothing — that's expected.

## ML task

A regression: `features → watts`, one model per architecture (x86 RAPL behaves
differently from ARM SBCs). The features are defined once in
`powerguess.model.FEATURES` and shared by the collector and the predictor, so a
trained model drops straight in.

A trained model ships as a small JSON of linear coefficients (no runtime ML
dependency — prediction is a dot product):

```json
{"intercept": 1.8, "coefficients": {"cpu_percent": 0.045, "cpu_freq_mhz": 0.0007, "n_cores": 0.6}}
```

Point the bridge at it with `MODEL_FILE=model.json`; readings then come from the
model instead of the idle/load curve. Richer model families can be added behind
the same `predict(features) -> watts` interface in `powerguess.model`.

## Publishing

The aggregated corpus is intended for the Hugging Face Hub (device-power
regression). Contributors with smart plugs or INA219 HATs can extend coverage
across architectures and peripherals — the more meters, the better every
meter-less device's estimate becomes.
