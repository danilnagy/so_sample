# FX over a run of notes

The [FX pattern observation](fx-pattern-control.md) held each effect on steps 5 to 12 of a
run of sixteen different keys. The backup equals the target exactly and the control run
plays key k on step k, one onset per step. Each step was read for which key sounded at
100 and 180 ms and how many onsets it had.

| FX | On steps 5 to 12 of the run |
| --- | --- |
| 1, 2, 15 | unchanged: keys 5 to 12 play as written |
| 3, 4 | unchanged here; on a single note they extend it, and each new step cuts the extension |
| 5 | two or three onsets per step, up to +7 dB: a doubled note |
| 6 | the pitch an octave below dominates, +1 to +6 dB: an octave-down copy added |
| 7 | pitch bent upward, reaching about an octave above the written key: an upward sweep |
| 8 | pitch bent downward, about an octave below the written key: a downward sweep |
| 9 | every note cut short, gone by 180 ms |
| 10 | of each four steps, the third starts late and the fourth is silent |
| 11, 12 | every step replays the key of step 5, where the effect began: a one-step loop |
| 13 | steps 7 and 11 carry a second, quieter onset of a note from two steps earlier |
| 14 | steps 5 to 12 replay keys 1 to 4 twice: a four-step loop from the pattern start |

Three effects, 1, 2 and 15, change nothing here, nor on a single note, nor in stereo or
harmonic content. Since 14 is a four-step loop and 11 and 12 one-step loops, these three
are most likely loops of 8, 12 and 16 steps, which replay exactly the written steps when
held on steps 5 to 12. The [loop length test](fx-loop-control.md) holds them over fifteen
steps, where any loop shorter than the pattern must show.

For a preview engine the measured behaviours above are what to reproduce; sweeps and
copies apply per note, loops replay earlier steps, 9 shortens and 10 gates.

- [Registration](../experiments/fx-pattern-registration-001.json)
- [Decision](../experiments/fx-pattern-decision-001.json)
- [Measurements](../experiments/compiled-fx-pattern-001/fx-pattern-measurements-001.json)
- [Observation](../experiments/compiled-fx-pattern-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-pattern-001/project.json`
