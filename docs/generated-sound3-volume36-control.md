# Complementary upper-interior ordering control

The generated18 result supports contiguous ordering. This new test is selected after
that result and registered before its own candidate backup and ordinary playback.
The existing uniform21 reference has already been observed; the registration says so
explicitly. Tone measurements reuse the original frozen band, fit window, thresholds,
pitch tolerance and loop tolerance.

The fixed candidate has contiguous code36 and alternate code9 in all16 Sound3 cells
of Pattern1. The models predict opposite directions relative to reference21:
contiguous36>21 predicts increased tone amplitude; alternate9<21 predicts decreased
amplitude. At least3% change must be consistent across all six measurements, with
pitch and loop stable. No exact gain ratio or curve is predicted.

Only first-byte0xc0 and second-byte0x0f masks change from the genuine reference.
Existing populated primary cells become`0df983`, and formerly empty parameter-only
cells become`000900`. All note-key bytes, other bits, samples, globals and other
patterns remain exact. The fixed constructor accepts only the exact verified
uniform21 body. No general volume setter is enabled.

The active folder is **`experiments/edited-sound3-volume36-002`**. Its target body is
`c0cc91737d5998aa5d6a214b1eeae0a46213b524d3f5fd307745d1bb780bd39c`.
Strict phase recovery and complete waveform/body/packet round trips pass. All23
focused volume tests pass, including source guards, key preservation, conflicting
channel directions, pitch/loop changes and retention of the uncertain user report.
Physical acceptance and amplitude direction remain pending.

The first preparation, folder`edited-sound3-volume36-001`, mistakenly labeled the
alternate code as18 rather than9. An independent test caught it before any restore
request or physical capture. Its original registration/report remain immutable,
and a [rejection](../experiments/edited-sound3-volume36-001/preparation-rejection-001.json)
records the semantic failure. Folder002 supersedes that preparation with corrected
metadata and explicit calculation of both orderings. Use only folder002.

## Physical action

1. Restore `experiments/edited-sound3-volume36-002/restore.wav` using the established
   stereo path and playback level. Keep both knobs and all audio settings unchanged.
2. Select Pattern1 / Sound3 / TONE, with playback stopped and write off.
3. Before playback, save a complete backup as
   `experiments/edited-sound3-volume36-002/capture.wav` at the established reduced
   recording level, with one second trailing silence.
4. Separately record12–15 seconds of ordinary Pattern1 playback as
   `experiments/edited-sound3-volume36-002/playback.wav`, then stop/write off.
5. Confirm restore success and recognizable phrase. Relative loudness can be
   reported as uncertain; do not guess or turn a knob to read a volume number.
   Leave both knobs untouched.

- [Active registration](../experiments/sound3-generated-volume36-registration-002.json)
- [Software validation](../experiments/edited-sound3-volume36-002/software-validation.json)
- [Existing frozen measurement method](../experiments/sound3-volume18-gain-method-registration-001.json)
- [Lower-interior result](generated-sound3-volume18-results.md)

After independent native decoding into`derived/analysis-001/capture.symbols.npz`:

```text
python -m scripts.check_generated_sound3_volume36
python -m scripts.sound3_volume_gain_analysis experiments/edited-sound3-volume36-002/playback.wav --out experiments/edited-sound3-volume36-002/playback-gain-results-001.json
python -m scripts.check_generated_sound3_volume36 --gain
```

Hardware observations remain separate from immutable software checks. Missing or
inconsistent data cannot be converted into support for a model.

## Completed reciprocal control

Physical reception is exact and all six frozen audio comparisons show approximately
2.20 times the reference tone amplitude with stable pitch and loop. The user confirms
pattern playback without a subjective gain-direction claim. See
[results](generated-sound3-volume36-results.md), the new bounded
[uniform volume operation](sound3-volume-edits.md), and the next
[post-playback persistence capture](sound3-volume-post-playback-control.md).
