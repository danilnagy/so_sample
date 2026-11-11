# Auditions after a restore: live values, untouched by patterns, never stored

Three sessions on 2026-11-08 with the [audition-lock restore](audition-lock-control.md):
Sound 16 key 1 holding a 200 Hz sawtooth, Pattern 1 playing it on four steps with the
web app's default locks (pitch 13, volume 36, filter 63, resonance 1).

1. **After the restore, pressing the key by hand made no sound.** Where the procedure
   called for four presses, the recording sits at the noise floor, 70 dB under the
   pattern's hits, before and after two pattern passes
   (`retake-001/attempts/playback-01.wav`). The pattern itself played at full level.
2. **Turning knob B fully clockwise made the key audible, and playing the pattern left
   that level alone.** Presses before and after two pattern passes are identical (RMS
   0.367, harmonic responses alike to 0.01 dB) and both differ from the pattern's hits
   (RMS 0.253). This is the predicted outcome, audition_keeps_live_state, measured over
   the three intended hit groups; the registered method saw a fourth group because
   PLAY was pressed again at the end, so the registered outcome is recorded as `other`
   ([result](../experiments/audition-lock-result-001.json)).
3. **None of it was stored.** A backup taken afterwards, with no restore in between,
   equals the registered target byte for byte: nothing_stored, as predicted
   ([result](../experiments/audition-knob-dump-result-001.json)).

Reading: a backup carries parameter locks only. A sound's live values, which auditions
by hand use, are left by a restore at a level that is inaudible, are not changed by
playing a pattern whose notes carry locks, are set by the sound's knobs, and are never
written to a backup. An editor cannot make auditions audible through a restore; after a
restore, select each sound and turn its volume knob.

Reception evidence for all three sessions comes from the web app's decoder
(`web/scripts/check-backup.ts`), which finds the preamble past the lead-in noise that
stops the harness decoder at the first packet. The harness decoder would need the same
preamble search to accept these backups on its own.

- [Control](audition-lock-control.md)
- [Registration](../experiments/audition-lock-registration-001.json)
- [Observation](../experiments/observe-audition-locks-001/hardware-observation-001.json)
- [Knob-dump registration](../experiments/audition-knob-dump-registration-001.json)
