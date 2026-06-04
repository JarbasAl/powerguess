# PowerGuess

Estimate the live power draw of a Linux device and publish it to MQTT with Home
Assistant auto-discovery — a power sensor for any headless box (Raspberry Pi, mini
PC, SBC, laptop) that has no smart plug.

PowerGuess picks the best available source and **labels every reading with where
it came from**, so a guess is never mistaken for a measurement. The core has no
Home Assistant dependency.

## Sources (best → fallback)

| Source | When | Accuracy |
| --- | --- | --- |
| INA219 (I²C) | a power-monitor HAT is wired (`pip install powerguess[ina219]`) | measured |
| `powerstat` (RAPL) | x86 with privileges | measured |
| Battery rails (`/sys`) | devices on battery | measured |
| CPU-load estimate | everything else (headless Pi, SBC, mini PC) | estimated, with an error band |

Every reading reports its `source` and, when estimated, an `error_margin`. The
estimate uses a per-device **calibration** (idle/peak watts) when available —
provided by hand, or learned automatically from a measured source over time — and
falls back to bundled per-model benchmark profiles. See
[docs/calibration.md](docs/calibration.md).

## Quick start (Home Assistant)

```bash
docker run -d --name powerguess --privileged --restart unless-stopped \
  -v /sys/class/power_supply:/sys/class/power_supply:ro \
  -e MQTT_HOST=192.168.1.10 \
  ghcr.io/jarbasal/powerguess:dev
```

Power, current, voltage (and battery) sensors appear automatically in Home
Assistant via MQTT discovery. See [docs/homeassistant.md](docs/homeassistant.md)
for entities, a dashboard card, and an energy-integration recipe. A
[`docker-compose.yml`](docker-compose.yml) with all options is included.

## Install

```bash
pip install powerguess
```

Run the bridge:

```bash
MQTT_HOST=192.168.1.10 python -m powerguess
```

## Library use

```python
from powerguess import PowerStatMonitor

def on_reading(reading):
    tag = reading.source if reading.measured else f"estimate ±{reading.error_margin}W"
    print(f"{reading.power:.1f} W  {reading.current:.2f} A  [{tag}]")

monitor = PowerStatMonitor()
monitor.add_callback(on_reading)
monitor.start()
```

## Better accuracy & data

- **[Calibration](docs/calibration.md)** — pin the estimate to your device
  (manual, auto-learned, or an INA219 measured path).
- **[Dataset](docs/dataset.md)** — `dataset.py` collects `features → measured
  watts` from metered devices to train a power-prediction model.

## Configuration

All settings are environment variables — see
[docs/configuration.md](docs/configuration.md). Common ones: `MQTT_HOST`,
`MQTT_USER`/`MQTT_PASSWORD`, `MEASURE_INTERVAL`, `CALIBRATION_FILE`,
`USE_INA219`, `DEVICE_NAME`, `DEVICE_ID`.

## License

Apache-2.0
