# Full 16-step effect map: first run and how the octave effect behaves

## First run: received exactly, registered result inconclusive

The [full step map](pattern1-FX-full-step-map-control.md) restore was received exactly
and its playback passed the protocol checks. The registered decision is inconclusive:

| Steps | Expected | Classified |
| --- | --- | --- |
| 2, 5, 10, 13: first of each effect pair | effect | effect, peak 1.43 times the reference |
| 3, 6, 11, 14: second of each effect pair | effect | indeterminate: too few windows above the gate |
| 1, 4, 7, 8, 9, 12, 15, 16 | none | none |

No step contradicts the sequential layout. See the
[decision](../experiments/pattern1-FX-full-step-map-decision-001.json).

## Exploratory reading: a crossfade into an exact octave

Pitch tracks over five loops, examined after the registered result:

- On the first step of an effect, the pitch climbs from 1.02 to about 1.54 times the
  reference while the level falls. This reads as a crossfade from the dry note into
  the transposed one.
- On a following effect step, the note plays at **exactly 2.00 times** the reference for
  about 100 ms, half its normal length, at about 0.16 of the recording's peak level. That
  matches the sample playing at double speed.
- On a step without the effect after an effect step, the pitch is back at 1.00 within
  about 20 ms.

The frozen method ignored windows below 20% of the recording's peak, so the quieter
octave notes were skipped. The person's report, "seems like 3 and 4", is kept verbatim.

## Next: confirmation with a per-note gate

The amended method gates each note at 20% of its own peak; everything else is unchanged.
On this run's playback, used only for development, it classifies all 16 steps as the
sequential layout predicts. A fresh backup and playback of the same device state, with
no restore, will decide it. See the
[confirmation registration](../experiments/pattern1-FX-full-step-map-confirm-registration-001.json)
and [method](../scripts/pattern1_fx_note_gate_method.py). Current genuine export:
`experiments/exported-pattern1-FX-full-step-map-001/project.json`.

## Confirmation run (-002): precondition failed on byte 131

The fresh backup without a restore differed from the target in one byte only: byte 131
of the second global record, 7 to 14. The previous session had stopped Pattern 1's
playback, which supports the hypothesis that this byte stores where Pattern 1 last
stopped. The registration required an exact backup, so its decision did not run. That
was a design error in the registration, not a device problem: runs without a restore
inherit playback-state bytes.

As an exploratory check, the frozen per-note-gate method classifies all 16 steps of the
fresh playback as the sequential layout predicts, five of five loops each. See the
[observation](../experiments/edited-pattern1-FX-full-step-map-002/hardware-observation-001.json).
The [step-effects writer test](step-effects-writer-control.md) restores first, so it
takes over as the registered confirmation.
