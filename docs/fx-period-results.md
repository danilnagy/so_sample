# FX periods: loops of 1/16, 1/12, 1/32 and 1/48 of a bar, retrigger every 1/16

The [FX period test](fx-period-control.md) held FX 1, 2, 3, 4 and 12 over long notes of the
four-segment sample at 60 BPM and tracked the pitch every 10 ms. The backup equals the
target exactly and the control note has no repetition period.

## Registered classification

| FX | Measured period | Classified |
| --- | --- | --- |
| 4 | 80 ms | 1/48 of a bar (83 ms) |
| 12 | 250 ms | 1/16 of a bar |
| 1, 2, 3 | none within the method's 60-cent limit | unresolved |

## Exploratory reading of the unresolved tracks

The frozen method scores a lag by the mean pitch difference, and the pitch estimate
glitches for one window at each loop boundary, which pushed FX 1, 2 and 3 over the limit.
The tracks themselves are plain to read:

| FX | Track | Period |
| --- | --- | --- |
| 1 | 140 ms of segment 1, then 80 to 100 ms of segment 2, repeating | about 250 ms, 1/16 of a bar |
| 2 | 140 ms of segment 1, then 180 ms of segment 2, repeating | about 333 ms, 1/12 of a bar |
| 3 | segment 1 with a boundary glitch every 120 ms, later alternating with segment 2 | about 125 ms, 1/32 of a bar |

FX 1 and 2 looped four and three times, one second in all, then let the sample run on,
so the loop acts on a moving portion rather than the sample start alone. These three
readings are exploratory; FX 4 and 12 are registered results.

So the loop family divides a bar: FX 1 loops 1/16, FX 2 1/12, FX 3 1/32 and FX 4 1/48 of
it, and FX 12 restarts the sample every 1/16. Whether these follow the tempo is the next
question.

- [Registration](../experiments/fx-period-registration-001.json)
- [Decision](../experiments/fx-period-decision-001.json)
- [Measurements](../experiments/compiled-fx-period-001/fx-period-measurements-001.json)
- [Observation](../experiments/compiled-fx-period-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-period-001/project.json`
