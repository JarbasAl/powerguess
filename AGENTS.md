# PowerGuess — agent onboarding

Estimate the live power draw of a Linux device and publish it to MQTT / Home
Assistant. The core is dependency-light (psutil, pexpect); the MQTT bridge adds
paho-mqtt; the OVOS PHAL integration is an optional extra.

**Org:** JarbasAl / **Branch:** dev (work) / master (stable)

## Layout

| Path | Purpose |
|------|---------|
| `powerguess/reading.py` | `Reading` frozen dataclass — value + provenance (`source`, `error_margin`) |
| `powerguess/guess.py` | `PowerStatMonitor` — source priority (ina219>powerstat>battery>estimate), energy, callbacks |
| `powerguess/calibration.py` | `Calibration` + `AutoCalibrator` (manual/file/env + learned idle/peak) |
| `powerguess/ina219.py` | optional INA219 I²C reader (`ina219` extra) |
| `powerguess/model.py` | `FEATURES`, `current_features`, `LinearPredictor` (pluggable estimate) |
| `powerguess/utils.py` | `/sys` battery reads, model detection, `transform_range` |
| `powerguess/models/*.json` | per-device idle/avg/load benchmark profiles |
| `powerguess/config.py` | env-var config |
| `powerguess/mqtt_client.py` | paho-mqtt client + HA auto-discovery (power/energy/source/…) |
| `powerguess/__main__.py` | CLI entry point (`python -m powerguess` / `powerguess`) |
| `dataset.py` | collect `features → measured watts` JSONL (root, per org convention) |
| `docs/` | Home Assistant, configuration, calibration, dataset docs |
| `test/` | offline pytest suite (battery `/sys` + INA219 SMBus mocked) |

## Conventions

- **Provenance is load-bearing:** every `Reading` records its `source`; estimates
  carry an `error_margin`. Never emit a guess that looks like a measurement, and
  never feed an estimate into the `AutoCalibrator` or `dataset.py` (ground truth
  only).
- No OVOS dependency anywhere — powerguess is a standalone power monitor.
- No `distutils` (removed in 3.12) — use `shutil.which`.
- Per-instance state only on `PowerStatMonitor` (no class-level mutable state).
- MQTT discovery mirrors the sibling bridges (`vad2mqtt`, `shazam2mqtt`):
  retained `homeassistant/<component>/<device_id>/<key>/config`.
- Tests are offline; mock `/sys/class/power_supply` reads (see `test_battery.py`).
  `__main__.py` is omitted from coverage.
- Versions bump from conventional-commit prefixes — never edit
  `powerguess/version.py`.
- CI is the shared `OpenVoiceOS/gh-automations` reusable workflows at `@dev`, plus
  a Docker build to GHCR.

## Run

```bash
pip install -e .[test]
pytest -q
MQTT_HOST=192.168.1.10 python -m powerguess
```
