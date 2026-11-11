# FX catalogue on a single note

The [FX catalogue observation](fx-catalog-control.md) played a 200 ms tone at 784 Hz with
one effect per note. The backup equals the target exactly and the control note is plain:
one onset, 784 Hz, gone by the next step. Each effect was described in 40 ms windows from
20 ms to 460 ms after the step, as level against the control and dominant pitch in cents
from 784 Hz. The person could hear the effects being applied but found them hard to tell
apart on single notes.

| FX | Measured on a single note |
| --- | --- |
| 3 | note extended to about 340 ms at full level, with a brief -38 cent dip around 120 ms |
| 4 | note extended to about 380 ms, with small pitch wobbles (-29, -17 cents) |
| 5 | a second onset 93 ms after the first, +8 dB where they overlap, slight detuning: a doubled note |
| 6 | +6 dB, dominant pitch alternating between 784 Hz and one octave below: an added octave-down copy |
| 7 | pitch rising through +166, +347, +530, +686 cents over 160 ms, then ending: an upward sweep |
| 8 | pitch falling through -170 to -1081 cents over 240 ms, lasting about 300 ms: a downward sweep |
| 9 | note cut after about 140 ms |
| 10 | note starts 165 ms late and lasts about 80 ms |
| 12 | note extended to about 260 ms with a -38 cent dip around 120 ms: a shorter version of 3 |
| 1, 2, 11, 13, 14, 15 | indistinguishable from the control in level, pitch and length |

The earlier reading of FX 7 as a crossfade to an exact octave came from a longer note; on
this 200 ms tone it reads as a sweep that reaches about +700 cents before the note ends.

Six effects leave a single note untouched, so they must act on the pattern as a whole:
loops, reverses or retriggers that need a run of different notes to show. The
[FX pattern observation](fx-pattern-control.md) plays each effect over a run of sixteen
different pitches.

- [Registration](../experiments/fx-catalog-registration-001.json)
- [Decision](../experiments/fx-catalog-decision-001.json)
- [Measurements](../experiments/compiled-fx-catalog-001/fx-catalog-measurements-001.json)
- [Observation](../experiments/compiled-fx-catalog-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-catalog-001/project.json`
