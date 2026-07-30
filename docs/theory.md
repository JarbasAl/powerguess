# How it works: the bounded estimate

PowerGuess rests on one idea: a device's power draw lives inside a known
envelope, and you can find that envelope cheaply. The estimate is an
interpolation within the envelope, not a number pulled from nowhere.

## The two bounds

- **Lower bound, idle power.** A powered-on device never draws less than it
  does at idle. Idle power is a stable, measurable floor.
- **Upper bound, the power supply.** The device cannot draw more, for any
  sustained period, than its PSU can deliver. The PSU's rated wattage is a
  hard ceiling. PSUs are usually over-provisioned, so the real peak is below
  the rating. A measured peak, when you have one, gives a tighter ceiling.

With two numbers, idle watts and the PSU rating, you already know the band the
device operates in:

```
idle_W  ≤  draw(t)  ≤  psu_W
```

## From bounds to an energy envelope

Bounds on instantaneous power give bounds on energy over any interval, with no
load information at all:

```
min energy over time T  =  idle_W × T
max energy over time T  =  psu_W  × T
```

That alone answers useful questions, such as "this Pi costs at most X and at
least Y per month," before any estimation happens.

## Where the estimate fits

Real draw moves between the floor and the ceiling with how hard the device is
working. PowerGuess places the estimate inside the envelope from CPU load and,
with a trained model, CPU frequency, core count, and other features:

```
idle_W ───────●────────────────── peak/psu_W
              ▲
        estimate at the current CPU load
```

The estimate is an interpolation between the bounds, not a measurement. That
is why every reading carries a `source` of `estimate` and an `error_margin`.
The margin comes from the width of the envelope. A wide idle-to-peak gap means
a less certain interpolation.

## Tightening the envelope

Each piece of information shrinks the band and sharpens the estimate.

| You provide | Lower bound | Upper bound | Estimate quality |
| --- | --- | --- | --- |
| nothing | generic profile | generic profile | rough |
| PSU rating | generic idle | measured ceiling (PSU) | bounded |
| + measured idle | measured floor | PSU | good floor |
| + measured peak (load test) | measured floor | measured ceiling | tight |
| + trained model | measured floor | measured ceiling | best interpolation |

Measuring idle and peak is what the [calibration wizard](calibration.md) does
with a smart plug. A measured source (INA219, RAPL, battery) skips estimation
entirely. See [calibration.md](calibration.md) for provenance.

## Why this matters

PowerGuess does not claim "your device draws 5.1 W." It claims "your device
draws between its idle floor and its supply ceiling, and right now CPU load
suggests roughly 5.1 W, with a margin set by how wide that band is."
Calibration narrows the band. A meter removes the guess. The number is always
anchored to physical bounds you can verify.

---
[Home](../README.md) · [Calibration →](calibration.md)
