# FX direction: reverse, sample loops, retrigger and scratch

The [FX direction test](fx-direction-control.md) held eight effects over long notes of a
four-segment sample whose pitch rises through the note. The backup equals the target
exactly, and every plain note played segments 1, 2, 3, 4 then silence.

| FX | Segment sequence in the five windows | Reading |
| --- | --- | --- |
| 15 | 4, 3, 2, 1, silence | **reverse**: the sample plays backwards |
| 1 | 1, 2, 2, 1, 1 and still sounding after the note | a loop of the sample's first 250 ms, a sixteenth of a bar at 60 BPM |
| 2 | 1, 2, 1, 2, 1 and still sounding | a loop of the first 333 ms, a twelfth of a bar |
| 3 | 1, 1, 1, 2, 1 and still sounding | a shorter loop; its length is not resolved by five windows |
| 4 | 1, 1, 1, 1, 1 or 1, 1, 2, 2, 2, varying between notes | a shorter loop still, varying with the note |
| 12 | 1, 1, 1, 1, 1 with 3 or 4 onsets per note | **retrigger**: the sample restarts repeatedly |
| 11 | 1, 2, 4, 1, 4 | **scratch**: the playback position jumps about the sample |
| 13 | 1, 2, 3, 4, silence | forward; its effect is on earlier steps, not the note itself |

The loop readings for FX 1 and 2 follow from where each window falls inside a repeating
250 or 333 ms stretch of the sample's start, which is exactly the observed sequences. The
loops run on past the note's own end while the effect is held.

The [FX period test](fx-period-control.md) measures the loop lengths of FX 1, 2, 3, 4 and
12 directly.

- [Registration](../experiments/fx-direction-registration-001.json)
- [Decision](../experiments/fx-direction-decision-001.json)
- [Observation](../experiments/compiled-fx-direction-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-direction-001/project.json`
