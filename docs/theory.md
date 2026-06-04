# How it works — the bounded estimate

PowerGuess rests on one idea: **a device's power draw lives inside a known
envelope, and you can establish that envelope cheaply.** The estimate is just an
interpolation *within* it — never a number pulled from nowhere.

## The two bounds

- **Lower bound — idle power.** A powered-on device never draws less than it does
  sitting idle. Idle power is a stable, measurable floor. Doing nothing is the
  cheapest the device gets.
- **Upper bound — the power supply.** The device physically cannot draw more,
  for any sustained period, than its PSU can deliver. The PSU's rated wattage is a
  hard ceiling. (PSUs are usually over-provisioned, so the *real* peak is below the
  rating — which is why a measured peak, when you have one, is a tighter ceiling.)

So with just two numbers — idle watts and the PSU rating — you already know the
band the device operates in:

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

That alone answers useful questions — "this Pi costs *at most* X and *at least* Y
per month" — before any estimation happens.

## Where the estimate fits

Real draw moves between the floor and the ceiling with how hard the device is
working. PowerGuess places it inside the envelope from CPU load (and, with a
trained model, CPU frequency, core count, …):

```
idle_W ───────●────────────────── peak/psu_W
              ▲
        estimate at the current CPU load
```

The estimate is an **interpolation between the bounds**, not a measurement — which
is exactly why every reading carries a `source` of `estimate` and an
`error_margin`. The margin is derived from the width of the envelope: a wide
idle→peak gap means a less certain interpolation.

## Tightening the envelope

Each piece of information shrinks the band and sharpens the estimate:

| You provide | Lower bound | Upper bound | Estimate quality |
| --- | --- | --- | --- |
| nothing | generic profile | generic profile | rough |
| PSU rating | generic idle | **measured ceiling (PSU)** | bounded |
| + measured idle | **measured floor** | PSU | good floor |
| + measured peak (load test) | measured floor | **measured ceiling** | tight |
| + trained model | measured floor | measured ceiling | best interpolation |

Measuring idle and peak is what the [calibration wizard](calibration.md) does with
a smart plug. A measured source (INA219, RAPL, battery) skips estimation entirely
— see [calibration.md](calibration.md) for provenance.

## Why this matters

The honest claim PowerGuess makes is not "your device draws 5.1 W." It is "your
device draws between its idle floor and its supply ceiling, and right now CPU load
suggests roughly 5.1 W (± a margin set by how wide that band is)." Calibration
narrows the band; a meter removes the guess. The number is always anchored to
physical bounds you can verify.
