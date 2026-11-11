# Voice priority: lowest sound numbers, with one exception

The [voice priority test](voice-priority-control.md) stacked eight sets of five or more
sounds. The backup equals the compiled target exactly. Every stack played exactly four
voices in all three cycles, so `four_voices` holds. No registered rule matched every
stack: `lowest_sounds_win` fails on one stack, and the other rules fail on most.

| Requested | Played |
| --- | --- |
| 1 2 3 4 11 | 1 2 3 11 |
| 1 2 3 4 16 | 1 2 3 4 |
| 1 2 3 4 5 | 1 2 3 4 |
| 4 5 6 7 8 | 4 5 6 7 |
| 1 11 12 13 14 | 1 11 12 13 |
| 1 2 11 12 13 | 1 2 11 12 |
| 11 12 13 14 15 | 11 12 13 14 |
| 1 2 3 11 to 16 | 1 2 3 11 |

Seven stacks follow "lowest sound numbers win". The exception is the pair of Sound 4 and
Sound 11: 11 wins, as it also did in the [polyphony test](polyphony-results.md). Sound 16
loses to Sound 4. Short-window readings show the losing voice never starts, so the choice
is made at the onset. All fourteen sounds have the same solo level, so loudness is not the
reason. The exception is recorded and unexplained.

For an editor: at most four sounds per step, and the lowest-numbered sounds take
precedence, with the 4 versus 11 pairing as a known exception.

- [Registration](../experiments/voice-priority-registration-001.json)
- [Decision](../experiments/voice-priority-decision-001.json)
- [Observation](../experiments/compiled-voice-priority-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-voice-priority-001/project.json`

The [voice stealing test](voice-steal-control.md) asks what happens across steps.
