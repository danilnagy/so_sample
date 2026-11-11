# Polyphony: four voices

The [polyphony test](polyphony-control.md) stacked up to fourteen distinct sounds on one
step. The backup equals the compiled target exactly.

## Registered method failure

The frozen method did not run on the playback. Its band-pass filter leaves a transient in
the first millisecond of the recording that exceeded the onset threshold, so it reported
that the recording did not start in silence. That failure is the registered result,
classified `method_failed_to_run`.

## Exploratory reading

A variant of the method that starts its onset search 20 ms into the recording found the
first note at 1.29 s and read all three cycles. Every stack of more than four sounds
played exactly four voices, in every cycle:

| Requested | Played |
| --- | --- |
| 1 2 | 1 2 |
| 1 2 3 4 | 1 2 3 4 |
| 1 2 3 4 5 6 | 1 2 3 4 |
| 1 to 8 | 1 2 3 4 |
| 1 to 8, 13, 14 | 1 2 3 4 |
| all fourteen | 1 2 3 11 |
| drums 11 to 16 | 11 12 13 14 |

The PO-33 plays **four voices at once**. Which four is not simply the lowest sound
numbers: with all fourteen stacked, Sound 11 played and Sound 4 did not. Voices that
played were within 0.6 dB of their solo level, so stacking does not lower them.

- [Registration](../experiments/polyphony-registration-001.json)
- [Decision](../experiments/polyphony-decision-001.json)
- [Exploratory reading](../experiments/polyphony-exploratory-001.json)
- [Observation](../experiments/compiled-polyphony-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-polyphony-001/project.json`

The [voice priority test](voice-priority-control.md) maps which four play.
