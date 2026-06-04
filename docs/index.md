# PowerGuess documentation

Estimate (or measure) the live power draw of a Linux device and publish it to
MQTT with Home Assistant auto-discovery — total power with provenance, a CPU/GPU
component breakdown, energy, and per-platform extras.

## Start here

- **[Theory](theory.md)** — the bounded-estimate model: power lives between an
  idle floor and a PSU ceiling; the estimate just interpolates within it.
- **[Home Assistant](homeassistant.md)** — the entities, dashboard cards, the
  energy dashboard, and MQTT topics.
- **[Configuration](configuration.md)** — every environment variable.

## Getting accurate numbers

- **[Calibration](calibration.md)** — pin the estimate to your device: the
  smart-plug wizard, battery auto-calibration (laptops, CPU+GPU), manual
  idle/peak, or idle + PSU rating.
- **[Dataset & model](dataset.md)** — collect `features → measured watts` and
  train a predictor with `train.py`.

## Components & platforms

- **[Component breakdown](components.md)** — the CPU and GPU as their own HA
  entities (utilization, temperature, frequency/VRAM, and validated power).
- **[Raspberry Pi / SBC](raspberry-pi.md)** — model profiles, Pi 5 PMIC power,
  INA219 HATs, and the throttling / overheating / overclocking sensors.
- **x86** — RAPL exposes CPU package power as a component; INA219 or a battery
  gives the measured total.

## Deploy

The bridge runs as a container — see [`docker-compose.yml`](../docker-compose.yml)
(includes the Raspberry Pi `vcgencmd` recipe) and the
[Pi deployment snippet](raspberry-pi.md#running-in-a-container).
