# Copy the calibration tone into an empty drum slot

Completed: the copy populates all16 candidate Sound9 groups with owner0 references.
Every preservation check passes with527 valid checksums; the first-group-only alternative
fails. See [copy results](drum9-copy-results.md) and the
[next slice control](drum9-key1-trim-min-control.md). Original instructions follow.

The current clean verified backup is the before-state. Sounds1/2/3/8 are populated;
the candidate sixteen selector groups for Sound9 are empty. All16 patterns and the
existing sample buffers must remain unchanged. One new capture is sufficient.

1. Keep **Pattern1**, playback stopped and write off. Select **Sound1** with
   **sound + 1**, then release.
2. Hold **write + sound**, press **9**, then release. This copies Sound1 into Sound9.
3. Reselect **Sound8 / TONE**. Leave both knobs and the successful retry recording
   settings unchanged.
4. **Before audition or pattern playback**, record a complete stereo backup as
   **experiments/event-015-b-copy-sound1-to-drum9/capture.wav**.

Leave the copied sound present afterward and report any deviation. Do not add notes,
record another sample or adjust slice boundaries during this control. The select/copy
combination follows the [official guide](https://teenage.engineering/guides/po-33/en)
and the previously used local copy controls.

The candidate mapping associates native selector IDs8..23 with Sound9's sixteen slices.
That is a hypothesis under test. Separate alternatives predict only the first group or
all16 groups will populate; another tests nine-byte owner0 reference records. No exact
slice boundaries, equal spacing, allocation behavior or target packet count is assumed.
Changes outside the candidate groups will be reported as preservation failures and
require reassessment. No drum editor or preview is enabled in advance.

- [Preregistered predictions](../experiments/drum9-copy-predictions-001.json)
- Baseline: `experiments/edited-quarter-window-001/capture-retry.wav`
- Baseline WAV SHA-256: `fa3c5f47983a46b1ce1a7f533eff7df94f6cdefed13efe7bafa6b5f190ff86cb`
- Baseline body SHA-256: `933eca1c290f4fcde0718ddf87e342c3f5b059bbb96d070f98fd6145c342699a`

Use stereo PCM16/44100Hz without effects. The successful retry input and levels are
sufficient; no new restore is needed before this copy control.
