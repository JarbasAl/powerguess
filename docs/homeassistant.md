# Home Assistant integration

PowerGuess publishes to MQTT with Home Assistant's MQTT discovery, so the
entities appear on their own when both PowerGuess and the
[MQTT integration](https://www.home-assistant.io/integrations/mqtt/) point at the
same broker. No YAML required.

## Entities

A single device, **PowerGuess** (`powerguess_01` by default), exposing:

| Entity | Unit | Device class |
| --- | --- | --- |
| `sensor.powerguess_power` | W | power |
| `sensor.powerguess_current` | A | current |
| `sensor.powerguess_voltage` | V | voltage |
| `sensor.powerguess_model` | — | — |

On devices with a battery it adds `battery_level` (%), `battery_power` (W),
`battery_status`, and the `charging` binary sensor.

Run more than one instance by giving each a unique `DEVICE_ID` / `DEVICE_NAME`
(and a distinct `MQTT_TOPIC_PREFIX`).

## Dashboard card

```yaml
type: entities
title: PowerGuess
entities:
  - entity: sensor.powerguess_power
    name: Power draw
  - entity: sensor.powerguess_current
    name: Current
  - entity: sensor.powerguess_voltage
    name: Voltage
  - entity: sensor.powerguess_model
    name: Device
```

A gauge for the live draw:

```yaml
type: gauge
entity: sensor.powerguess_power
name: Power draw
unit: W
min: 0
max: 15
severity:
  green: 0
  yellow: 8
  red: 12
```

## Energy dashboard

The power sensor carries `state_class: measurement`, so a Riemann-sum helper
turns it into the cumulative energy the Energy dashboard needs:

```yaml
# configuration.yaml
sensor:
  - platform: integration
    source: sensor.powerguess_power
    name: powerguess_energy
    unit_prefix: k
    round: 3
    method: trapezoidal
```

Add `sensor.powerguess_energy` under **Settings → Energy → Individual devices**.

## MQTT topics

| Topic | Payload |
| --- | --- |
| `powerguess/state` | `{"power", "voltage", "current", "timestamp"}` |
| `powerguess/battery` | `{"level", "status", "charging", "power", "voltage"}` |
| `powerguess/model` | `{"model"}` |
| `homeassistant/sensor/<id>/<key>/config` | discovery (retained) |

Topic prefix and discovery prefix are configurable
([configuration](configuration.md)).
