# Voice release: a voice frees up in its last 100 ms

The [voice release test](voice-release-control.md) varied how much time the three short
notes had left when a fifth note arrived, with a long note sounding throughout. The backup
equals the compiled target exactly. This was the first test on the slim package: 212992
sample codes, a 62 s restore.

| Time left on the short notes | Fifth note | Long note | Short notes |
| --- | --- | --- | --- |
| 417 ms | dropped | continues | all continue |
| 222 ms | dropped | continues | all continue |
| 84 ms | plays | continues | ended before the window |
| ended 14 ms earlier | plays | continues | ended |

`release_under_100ms` holds on every voice of every scenario; the other three models fail.
Every voice that played was within 0.5 dB of its solo level.

So the PO-33 never cuts a sounding voice to make room. A new note gets a voice only if one
is free or within roughly 100 ms of its end, between 84 and 222 ms by this test, and is
otherwise dropped. New notes on one step take free voices in order of sound number.

For an editor: with four voices, a step can start as many notes as there are voices free
or about to finish; the rest are silent, and nothing already sounding is affected.

- [Registration](../experiments/voice-release-registration-001.json)
- [Decision](../experiments/voice-release-decision-001.json)
- [Observation](../experiments/compiled-voice-release-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-voice-release-001/project.json`

The [note bits test](note-bits-control.md) covers pitch code 0 and the unknown bit 5.
