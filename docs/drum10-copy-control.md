# Test a second drum selector block

Completed: the clean retry passes all preservation checks and all separate predictions
with543 valid checksums. Sound10 is independently localized to selectors24..39; its
references exactly match the original Sound9 autocopy. See
[copy results](drum10-copy-results.md) and the
[next slice-copy control](cross-drum-slice-copy-control.md). The failed first recording
and diagnostics remain archived. Earlier failure status and instructions follow.

The first capture cannot verify the copy yet: crossing decode fails late at native
byte84618, and measured-clock recovery fails quarter-model checks. Fixed waveform-only
windows250/500/1000 show the same late discontinuity on both channels. Four identical
consecutive stereo frames occur there; removing only the three repeats as a diagnostic
still does not recover a valid frame. The exact cause remains unidentified. The original
WAV is archived as `capture-attempt-001.wav`, with all failed artifacts and diagnostic
outputs retained. No Sound10 hypotheses have been evaluated or mapping enabled. See
[capture status](../experiments/event-018-b-copy-sound1-to-drum10/capture-verification-status-001.json).

**Next action:** keep the current copied device state and both knobs untouched. Do not
repeat the copy or restore. With Sound8/TONE, write off and playback stopped, record
another complete backup as **experiments/event-018-b-copy-sound1-to-drum10/capture-retry.wav**.
Begin recording before transmission and leave a second of silence after the entire dump
finishes before stopping. Use the successful stereo input/settings, PCM16/44100Hz and
no effects. [Retry registration](../experiments/event-018-b-copy-sound1-to-drum10/recapture-retry-registration.json)
retains the original hypotheses without substituting missing data. Original instructions follow.

The current clean verified backup is the before-state. Sound1 remains the full calibration
source, Sound9 keys1/2 retain their accepted2000-code windows, and candidate Sound10
selector groups24..39 are empty. One copy and one new backup are sufficient.

1. Keep **Pattern1**, playback stopped and **write off**. Select **Sound1** with
   **sound + 1**, then release.
2. Hold **write + sound**, press **10**, then release to copy Sound1 into Sound10.
3. Reselect **Sound8 / TONE**. Retain both knob positions and the successful retry
   recording setup.
4. **Before audition or pattern playback**, record a complete stereo backup as
   **experiments/event-018-b-copy-sound1-to-drum10/capture.wav**.

Leave the copied sound present and report any deviation. The selection/copy combination
follows the [official guide](https://teenage.engineering/guides/po-33/en) and the prior
Sound1-to-Sound9 control. No additional restore is needed.

Preservation checks permit new data only under candidate selector IDs24..39. Existing
sample buffers/references, both Sound9 windows, all16 patterns, selector order and every
unrelated packet must remain unchanged. No exact added packet count is a preservation
requirement, so new allocation or layout behavior remains visible rather than hidden.

Separate hypotheses predict that Sound10 uses this block, all16 groups populate with
nine-byte owner0 references, and their raw records exactly match the **original** Sound9
autocopy before its later edits. That prediction uses the retained first-copy artifact,
not the now-trimmed Sound9 records. A further hypothesis predicts16 new packets/224 body
bytes. Different allocation, boundaries or failed predictions will be reported explicitly.

- [Preregistered predictions](../experiments/drum10-copy-predictions-001.json)
- Baseline: `experiments/edited-drum9-key2-end-001/capture-retry.wav`
- Baseline WAV SHA-256: `447b8e92224fd5db41f53bb283bff66317da14a32bf9b0004669aed057cfec91`
- Baseline native body SHA-256: `1f3295c4cc8150d75a1513c76d996c54ed460c9b9d26730c556d7da24065ad28`

Use stereo PCM16/44100Hz without effects. This registration does not enable individual
Sound10 key mapping, a Sound10 writer/preview or a general autoslice formula in advance.
