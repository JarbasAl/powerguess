# PowerGuess

Estimate the live power draw of a Linux device and publish it to MQTT with Home
Assistant auto-discovery — a power sensor for any headless box (Raspberry Pi, mini
PC, SBC, laptop) that has no smart plug.

PowerGuess reads `powerstat` when it's available and privileged, falls back to a
per-model CPU-load estimate otherwise, and reads battery rails directly from
`/sys/class/power_supply`. The core has no Home Assistant or OVOS dependency.

## How it estimates

| Source | When | Accuracy |
| --- | --- | --- |
| `powerstat` (RAPL) | x86 with privileges | live, accurate |
| Battery rails (`/sys`) | devices with a battery | live, accurate |
| Per-model CPU-load curve | everything else (Pi, SBC, mini PC) | estimate from bundled benchmarks |

Bundled benchmark profiles cover the Raspberry Pi family and generic
laptop / SBC / mini-PC / PC fallbacks.

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
pip install powerguess          # core + MQTT bridge
pip install powerguess[phal]    # + OVOS PHAL sensor integration
```

Run the bridge:

```bash
MQTT_HOST=192.168.1.10 python -m powerguess
```

## Library use

```python
from powerguess import PowerStatMonitor

def on_reading(reading, model):
    power, voltage, current = reading
    print(f"{power:.1f} W  {current:.2f} A  {voltage:.1f} V")

monitor = PowerStatMonitor()
monitor.add_callback(on_reading)
monitor.start()
```

## Configuration

All settings are environment variables — see
[docs/configuration.md](docs/configuration.md). Common ones: `MQTT_HOST`,
`MQTT_USER`/`MQTT_PASSWORD`, `MEASURE_INTERVAL`, `DEVICE_NAME`, `DEVICE_ID`.

## License

Apache-2.0
