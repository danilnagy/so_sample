# Voice stealing: a sounding note is not cut while it has time left

The [voice stealing test](voice-steal-control.md) ran twice. In the first session the
device did not take the restore; its backup equalled the previous state and is archived.
The second session's backup equals the compiled target exactly.

## Registered result: invalid for the long notes

The registration predicted the key-13 notes one octave below key 1. The
[verified layout](pattern1-key-scale-map-results.md) puts key 13 at 19 semitones below,
so Sound 1 and Sound 8 at key 13 played at 200.0 and 366.8 Hz, half the stored rate, for
1.0 s. The registered method measured noise at the predicted frequencies, so its readings
of the two long notes are meaningless and no model matched. That stands as the registered
outcome. The readings of the other voices are valid.

## Exploratory re-read at the correct frequencies

| Scenario | At the overflow | Long note | New note | Taken from |
| --- | --- | --- | --- | --- |
| A | long + 3 notes with 84 ms left, Sound 5 arrives | continues | plays | a short note |
| B (control) | four voices, no overflow | continues | plays | nothing |
| C | long + 3 drums with 22 ms left, Sound 1 arrives | continues | plays | a short note |
| D | long with 500 ms left, Sounds 1 2 3 4 arrive | continues | 1 2 3 play, 4 dropped | nothing |

The long note survived every overflow, so the device does not cut a sounding voice to make
room. A fifth note still plays when another voice is within 84 ms of its end, and is
dropped when the only busy voice has 500 ms left. Among new notes on one step, the
lowest sound numbers take the free voices and the rest are dropped.

For an editor: a note is safe once it is sounding, and a step can start at most as many
new notes as there are voices free or about to finish.

- [Registration](../experiments/voice-steal-registration-001.json)
- [Decision](../experiments/voice-steal-decision-001.json)
- [Exploratory re-read](../experiments/voice-steal-exploratory-001.json)
- [Observation](../experiments/compiled-voice-steal-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-voice-steal-001/project.json`

The [voice release test](voice-release-control.md) brackets the time left that makes a
voice available.
