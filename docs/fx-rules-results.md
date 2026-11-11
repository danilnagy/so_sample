# FX 14 loops the steps before the hold; FX 13 is a triplet quantize

The [FX rules test](fx-rules-control.md) held FX 14 from four different steps and FX 13 over
a full run of sixteen keys. The backup equals the target exactly and the control run is
plain.

## FX 14: registered rule confirmed

`loop_steps_before_hold` matches every held step of all four patterns; the other two
rules fail.

| Hold from step | Heard on the held steps |
| --- | --- |
| 3 | 1, 2, 1, 2, ... |
| 5 | 1, 2, 3, 4, 1, 2, 3, 4, ... |
| 7 | 1 to 6, 1 to 6, ... |
| 9 | 1 to 8, 1 to 8 |

While FX 14 is held, the pattern replays the steps that came before the hold, from step 1,
in a loop whose length is the hold's start step minus one. Releasing it resumes the
written steps.

## FX 13: a triplet quantize, read from the timing

All three registered rules fail, because they predicted which key sounds and not when.
The keys heard at 30 and 100 ms into each step, with the onset counts, show the timing:

| Beat of steps 5 to 8 | Heard |
| --- | --- |
| step 5 | key 5 on time |
| step 6 | key 5 still at 30 ms, key 6 by 100 ms: the note starts about a third of a beat late |
| step 7 | key 6 still sounding at 30 ms; two onsets in the step |
| step 8 | key 7, not 8 |
| step 9 | key 9 on time: the next beat starts normally |

The same shape repeats for steps 9 to 12 and 13 to 16, and it is the shape seen at 120 BPM
too. So FX 13 plays the first three notes of each beat at triplet spacing, 0, 1/3 and 2/3
of the beat, and drops the fourth: a 6/8, or triplet, quantize. The earlier readings of an
"echo" were the second triplet note heard inside the third step.

Both open questions from the [FX reference](fx-reference.md) are closed, FX 14 by its
registered rule and FX 13 by an exploratory reading of the same data.

- [Registration](../experiments/fx-rules-registration-001.json)
- [Decision](../experiments/fx-rules-decision-001.json)
- [Observation](../experiments/compiled-fx-rules-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-rules-001/project.json`
