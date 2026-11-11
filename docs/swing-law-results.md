# Swing law: even steps are delayed by code/24 of a step

The [swing law test](swing-law-control.md) set swing to 18 at 60 BPM with a 57 ms click
on every step. The backup equals the compiled target exactly.

Over five loops and all eight even steps, each even click sat at position 0.874 of the
interval between its odd neighbours, a delay of 0.749 steps, with a spread of 0.003.
`linear_in_code` holds, predicting 0.872; the triplet and three-quarter models fail. The
loop length was 250.03 ms per step.

With the earlier swing-6 measurement at 137 BPM, which delayed the even steps by 0.248
steps, two points on the scale agree with one rule:

**Even steps are delayed by swing / 24 of a step.** Swing 18, the maximum, delays them by
three quarters of a step, far past a triplet feel. Odd steps stay on the grid and the loop
length is unchanged.

The byte is linear in code and relative to tempo. `set_swing_byte` writes it in any global
layout; the older `set_swing` keeps its opaque-context guard.

- [Registration](../experiments/swing-law-registration-001.json)
- [Decision](../experiments/swing-law-decision-001.json)
- [Measurements](../experiments/compiled-swing-law-001/swing-measurements-001.json)
- [Observation](../experiments/compiled-swing-law-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-swing-law-001/project.json`

The [priority map test](priority-map-control.md) returns to the voice priority exception.
