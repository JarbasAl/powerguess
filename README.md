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
| RAPL (`/sys/class/powercap`) | x86 with a readable energy counter (auto-detected) | measured |
| `powerstat` | x86 fallback when RAPL isn't readable | measured |
| Battery rails (`/sys`) | devices on battery | measured |
| CPU-load estimate | everything else (headless Pi, SBC, mini PC) | estimated, with an error band |

On a machine with an NVIDIA GPU it also breaks the **GPU out as its own
component** — utilization, temperature, VRAM, and (when `nvidia-smi` reports a
credible value) GPU power — as separate Home Assistant entities.

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

## How it works

Power lives between two bounds: an **idle floor** (the device never draws less)
and the **PSU ceiling** (it can't draw more). Those two numbers already bracket
its energy use; the estimate just interpolates a point between them from CPU load.
See **[docs/theory.md](docs/theory.md)** — it's the model the whole tool is built
on.

## Better accuracy & data

- **[Calibration](docs/calibration.md)** — pin the bounds to your device. The
  `powerguess-calibrate` wizard measures idle and peak with an MQTT smart plug
  and writes the calibration for you; or supply them by hand, learn them
  automatically from a measured source, or read an INA219.
- **[Dataset](docs/dataset.md)** — `dataset.py` collects `features → measured
  watts` from metered devices to train a power-prediction model.

## Configuration

All settings are environment variables — see
[docs/configuration.md](docs/configuration.md). Common ones: `MQTT_HOST`,
`MQTT_USER`/`MQTT_PASSWORD`, `MEASURE_INTERVAL`, `CALIBRATION_FILE`,
`USE_INA219`, `DEVICE_NAME`, `DEVICE_ID`.

## License

Apache-2.0
