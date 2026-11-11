# Drum-notes writer verified: key k plays slice k

The [drum-notes writer test](drum-notes-writer-control.md) wrote drum Sound11 key k on
step k of Pattern 1 through the public `set_drum_notes` plan operation, with auxiliary
byte 0x10 + k - 1. The backup equals the compiled target exactly.

Playback, measured with the frozen grid method over five loops:

| Step | Expected cents | Measured cents | Hz |
| --- | --- | --- | --- |
| 1 | 0 | 0.0 | 399.9 |
| 2 | 150 | 150.2 | 436.2 |
| 8 | 1050 | 1050.1 | 733.5 |
| 16 | 2250 | 2250.1 | 1467.1 |

Every step is within 0.3 cents of `key_k_plays_slice_k` in all five loops;
`every_key_plays_slice_1` fails. Step 1 sounds at 399.9 Hz, 0.2 cents from the recorded
400 Hz burst: drums at pitch code 13 play their recording at the stored rate, unlike
melodic sounds, which sound 7 semitones higher at key 1. The person heard a rising run of
16 beeps.

So all 16 drum keys use auxiliary byte 0x10 + key - 1, and key k plays the k-th window
of the kit. `set_drum_notes` is hardware verified for Sound11 with one parameter set.

An exploratory duration reading of the same playback suggests each slice stops at its
window end: several steps sound exactly as long as their window, including the start of
the next burst that the device's onset-placed boundary cut into. The
[drum-kit import test](drum-kit-import-control.md) registers this as a prediction.

- [Registration](../experiments/drum-notes-registration-001.json)
- [Decision](../experiments/drum-notes-decision-001.json)
- [Observation](../experiments/compiled-drum-notes-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-drum-notes-001/project.json`
