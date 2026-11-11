# Aux nibble 3: under swing a note's time ends on the unswung grid (all registered rules failed)

Session 2026-11-11, [registered design](aux-nibble-3-control.md), following
[aux nibble](aux-nibble-results.md) and [aux nibble 2](aux-nibble-2-results.md). At 120 BPM
(a step is 125 ms) with swing 12, so even steps start 62.5 ms late. The backup equalled the
compiled target exactly on its first recording; four passes were measured.

**None of the six registered hypotheses held.** They are kept as failed. The measurements
follow a rule none of them stated, given below as an exploratory reading.

| Prediction | Result |
| --- | --- |
| Reception: the backup equals the target exactly | **held** |
| Spacing scales with the step: retrigger n spaced 125/n ms on odd and even steps | **failed** (held on every case but one: retrigger 2 on an even step played a single hit) |
| Spacing spans the swung step: odd 187.5/n, even 62.5/n ms | **failed** |
| Spacing fixed in time: 250/n ms | **failed** |
| Length scales with the step: n × 125 ms on odd and even steps | **failed** (held on odd steps; even steps were 62.5 ms shorter) |
| Length ends on the swung grid: odd n plus 62.5 ms, even n minus 62.5 ms | **failed** |
| Length fixed in time: n × 250 ms | **failed** |

## Measurements

| Retrigger | 2 | 3 | 4 | 6 | 8 (exploratory) |
| --- | --- | --- | --- | --- | --- |
| Spacing, odd step (ms) | 62.9 | 41.7 | 31.4 | 20.5 | 15.0 |
| Spacing, even step (ms) | (one hit) | 41.7 | 31.4 | 20.9 | 15.3 |
| Onsets, odd step | 2 | 3 | 4 | 6 | 8 |
| Onsets, even step | 1 | 2 | 2 | 3 | 4 |

| Melodic length (steps) | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- |
| Odd step (ms) | 130 | 254 | 382 | 506 |
| Even step (ms) | 65 | 192 | 314 | 442 |

Odd steps started on the grid (within 2 ms); even steps 63 to 64 ms after it, the swing.

## Exploratory reading: the note's time ends on the unswung grid

Not a registered hypothesis; stated after seeing the data, and fitting every measurement
above within a few milliseconds:

- **Spacing** is the step divided by the count: 125/n ms here, as 250/n was at 60 BPM in
  [aux nibble](aux-nibble-results.md).
- **A drum's repeats** start at the note's sounded (swung) onset, one every step/n, and
  stop at the next step's unswung start. On an odd step all n fit; on a step delayed by
  62.5 ms only those before the next grid line play: 2→1, 3→2, 4→2, 6→3, 8→4.
- **A melodic note** ends at its step's unswung start plus n steps: n × 125 ms on an odd
  step, n × 125 − 62.5 ms on a delayed one.

In short, swing delays where a note starts but not where its time ends. The rule should be
confirmed by a registered session at another swing value and tempo before it is treated as
settled.

## Limits

- One session, one device, one tempo and one swing value.
- Retrigger 8 at 120 BPM (15.6 ms apart) is close to the method's resolution and is
  exploratory.
- No session observations were noted.

- [Registration](../experiments/aux-nibble-registration-003.json)
- [Decision](../experiments/aux-nibble-decision-003.json)
- [Observation](../experiments/aux-nibble-003/hardware-observation-001.json)
