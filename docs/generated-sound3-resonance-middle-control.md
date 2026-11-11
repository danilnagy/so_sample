# Generated B32 interior at fixed low-pass16

The current accepted state is low-pass16/B63. The new research target changes only
third-primary bits2..7 to raw32 in all16 Sound3/Pattern1 cells. Cutoff16, pitch14,
volume36 and every other state bit remain exact. Both software phase and whole
native body/packet recovery pass; this new target is not yet hardware-verified.

1. Restore `experiments/edited-sound3-filter16-B32-middle-001/restore.wav` using the
   established stereo setup and playback level. Keep both knobs and all recording
   settings unchanged.
2. Before ordinary playback, save a complete backup as
   `experiments/edited-sound3-filter16-B32-middle-001/capture.wav` at the established
   reduced level with one second trailing silence.
3. Select Pattern1 / Sound3 / FILTER without moving either knob. Separately record
   12–15 seconds of ordinary Pattern1 playback as
   `experiments/edited-sound3-filter16-B32-middle-001/playback.wav`, then stop and
   ensure write is off. Report what you actually hear, including uncertainty.

No WRITE-held pass or guessed comparison with remembered endpoints is required.
Do not move B to a physical midpoint or change levels to force an expected result.
The whole native target is
`d039d344987f852ad3a8668249fab8a1366e1d1e9bc9280c789d0059947ca73f`.

The new hypothesis predicts middle amplitude strictly between the observed endpoint
measurements with margins: middle/minimum at least1.05, and maximum/middle at
least1.05, in all six common channel/threshold comparisons. Frequency and loop
consistency retain their0.5% and5ms limits. The original common measurement method
and windows remain unchanged. Failed bounds, missing or unusable audio are retained
without refitting. A pass would support an interior effect at this cutoff, without
proving proportional Q, numeric UI midpoint or a complete resonance law.

Both endpoint audio sets were already observed before this new registration; that
fact is explicit. Their WAVs, native reports, artifacts, observations and audio
reports are hash-pinned. Raw32 has bit7 set while bits2..6 are clear; this tests a
new interior value without assuming bit7's general role. Public guards remain
unchanged and no general resonance writer is enabled.

- [Preregistration and frozen endpoint identities](../experiments/sound3-generated-filter16-B32-middle-registration-001.json)
- [Software validation](../experiments/edited-sound3-filter16-B32-middle-001/software-validation.json)
- [Constructor](../scripts/prepare_generated_sound3_resonance_middle.py)
- [Native/audio checker](../scripts/check_generated_sound3_resonance_middle.py)
- [Accepted endpoint comparison](generated-sound3-resonance-pair-results.md)

After independent threshold0.0063 decoding, run
`python -m scripts.check_generated_sound3_resonance_middle`, then
`python -m scripts.check_generated_sound3_resonance_middle --audio`.
All reports are immutable and hardware-unverified. All110 affected checks pass;
production code is unchanged since the full1,025-test run.

## Completed

B32 recaptures the entire target and every packet. Both frozen component-amplitude
bounds pass with consistent frequency and loop; the user confirms the pattern
remains audible, without a subjective endpoint ranking. See
[results](generated-sound3-resonance-middle-results.md),
[guarded public editing](sound3-resonance-edits.md) and the
[next saved-FX control](pattern1-FX-probe-control.md). Original registration and
reports remain unchanged.
