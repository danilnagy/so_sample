# Loop length test: FX 1, 2 and 15 are not loops

The [loop length test](fx-loop-control.md) held FX 1, 2, 15, 14 and 11 over steps 2 to 16
of the sixteen-key run. The backup equals the target exactly and the control run plays
key k on step k.

| FX | Held from step 2 | Reading |
| --- | --- | --- |
| 1 | keys 1 to 16 as written | identity, loop_16 |
| 2 | keys 1 to 16 as written | identity, loop_16 |
| 15 | keys 1 to 16 as written | identity, loop_16 |
| 14 | key 1 on every step | loop_1 |
| 11 | key 2, the first held step, on every step | unresolved against the registered loops |

FX 1, 2 and 15 replay the written steps whether held from step 5 or step 2, so they are
not loops of any length. FX 14 is not a fixed four-step loop either: held from step 5 it
replayed keys 1 to 4, held from step 2 it replays key 1 only, so it restarts the pattern
from the hold and the period depends on where the hold begins. FX 11 keeps repeating the
step on which the effect began.

A pure tone cannot show reversed playback or loops of a portion of a sample, so the three
silent effects, and the extending effects 3, 4 and 12, are next tried on a sample whose
pitch changes through the note ([FX direction test](fx-direction-control.md)).

- [Registration](../experiments/fx-loop-registration-001.json)
- [Decision](../experiments/fx-loop-decision-001.json)
- [Observation](../experiments/compiled-fx-loop-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-loop-001/project.json`
