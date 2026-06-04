# PowerGuess — agent onboarding

Estimate the live power draw of a Linux device and publish it to MQTT / Home
Assistant. The core is dependency-light (psutil, pexpect); the MQTT bridge adds
paho-mqtt; the OVOS PHAL integration is an optional extra.

**Org:** JarbasAl / **Branch:** dev (work) / master (stable)

## Layout

| Path | Purpose |
|------|---------|
| `powerguess/guess.py` | `PowerStatMonitor` — powerstat / battery / CPU-load estimate, callbacks |
| `powerguess/utils.py` | `/sys` battery reads, model detection, `transform_range` |
| `powerguess/models/*.json` | per-device idle/avg/load benchmark profiles |
| `powerguess/config.py` | env-var config for the MQTT bridge |
| `powerguess/mqtt_client.py` | paho-mqtt client + Home Assistant auto-discovery |
| `powerguess/__main__.py` | CLI entry point (`python -m powerguess` / `powerguess`) |
| `powerguess/sensors.py`, `device.py` | OVOS PHAL sensors — **`phal` extra only** |
| `docs/` | Home Assistant + configuration docs |
| `test/` | offline pytest suite (battery/`/sys` reads mocked) |

## Conventions

- The core (`guess`, `utils`, `mqtt_client`, `config`, `__main__`) must not import
  OVOS. PHAL code stays in `sensors.py` / `device.py` behind the `phal` extra.
- No `distutils` (removed in 3.12) — use `shutil.which`.
- MQTT discovery mirrors the sibling bridges (`vad2mqtt`, `shazam2mqtt`):
  retained `homeassistant/<component>/<device_id>/<key>/config`.
- Tests are offline; mock `/sys/class/power_supply` reads (see `test_battery.py`).
  `sensors.py`/`device.py`/`__main__.py` are omitted from coverage.
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
