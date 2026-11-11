# Priority map: Sound 11 ranks after Sound 3

The [priority map test](priority-map-control.md) pitted each drum against melodic Sounds 1
to 4, and Sound 11 against Sound 5. The backup equals the compiled target exactly. Every
stack played exactly four voices.

| Requested | Played |
| --- | --- |
| 1 2 3 4 11 | 1 2 3 11 |
| 1 2 3 4 12 | 1 2 3 4 |
| 1 2 3 4 13 | 1 2 3 4 |
| 1 2 3 4 14 | 1 2 3 4 |
| 1 2 3 4 15 | 1 2 3 4 |
| 1 2 3 4 16 | 1 2 3 4 |
| 1 2 3 5 11 | 1 2 3 11 |
| 2 3 4 5 11 | 2 3 4 11 |

`sound11_outranks_4_and_5` holds on every stack and `lowest_sounds_win` fails. Drums 12 to
16 all lose to Sound 4, so the voice ranking when more than four sounds share a step is
1, 2, 3, 11, 4, 5, 6, 7, 8, 12, 13, 14, 15, 16, with Sounds 9 and 10 untested. Sound 11's
place relative to Sounds 1 to 3 cannot be told from which four play, and does not matter
for an editor. Why Sound 11 is special is unknown; its kit was imported the same way as
the others and plays at the same level.

- [Registration](../experiments/priority-map-registration-001.json)
- [Decision](../experiments/priority-map-decision-001.json)
- [Observation](../experiments/compiled-priority-map-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-priority-map-001/project.json`
