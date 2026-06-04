# Configuration

All settings are environment variables, read once at startup.

## Monitor

| Variable | Default | Meaning |
| --- | --- | --- |
| `MEASURE_INTERVAL` | `5` | seconds between measurements |
| `PUBLISH_INTERVAL` | `5` | minimum seconds between MQTT publishes |
| `SMOOTH` | `false` | rolling-average the powerstat readings |
| `PREFER_BATTERY` | `false` | trust battery rails over the estimate when discharging |

## MQTT

| Variable | Default |
| --- | --- |
| `MQTT_HOST` | `localhost` |
| `MQTT_PORT` | `1883` |
| `MQTT_USER` / `MQTT_PASSWORD` | _(none)_ |
| `MQTT_TOPIC_PREFIX` | `powerguess` |
| `MQTT_CLIENT_ID` | `powerguess-client` |
| `MQTT_QOS` | `0` |
| `MQTT_RETAIN` | `true` |
| `MQTT_KEEPALIVE` | `60` |
| `MQTT_RETRY_COUNT` | `5` |
| `MQTT_RETRY_MAX_BACKOFF` | `30` |
| `MQTT_CONNECT_TIMEOUT` | `2.0` |

## Home Assistant

| Variable | Default |
| --- | --- |
| `HA_ENABLED` | `true` |
| `HA_DISCOVERY_PREFIX` | `homeassistant` |
| `DEVICE_NAME` | `PowerGuess` |
| `DEVICE_ID` | `powerguess_01` |

## Logging

| Variable | Default |
| --- | --- |
| `LOG_LEVEL` | `INFO` |
