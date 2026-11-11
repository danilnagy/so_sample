# Return Sound3 to full trim length

The current state retains sounds1/2/3/8, with Sound3 length at minimum, Sound8 selected,
FX in TONE, empty Pattern1, write off and playback stopped.

1. Select **Sound3** using **sound + 3**, then release.
2. Press **FX** until **tri/TRIM** appears. Turn **knob B fully clockwise** to set the
   length to its maximum, leaving knob A untouched.
3. Return FX to **TONE**, reselect **Sound8**, retain empty Pattern1/write off/stopped
   playback, and leave the knobs in place. Keep recording settings/master volume unchanged.
4. Record one complete stereo backup as
   **experiments/empty-001-g-sound3-trim-return/capture.wav**.

The [official guide](https://teenage.engineering/guides/po-33/en) identifies knob B as
sound length in TRIM mode. Leave the four sounds present afterward and report deviations.

This is an A-return hypothesis: maximum trim length should reproduce the original
untrimmed Sound3 reference. The original and the current minimum-length capture are both
pinned in ../experiments/sound3-trim-return-predictions-001.json before upload. Require
the original prefix[0,178795) exactly on both channels, covering the last nonconstant
transition's contributing coordinates; compare complete arrays/counts separately.
No shift, phase correction, padding or tail trimming is permitted to force agreement.

If the knob endpoint differs from the original default's serialization, that prediction
may fail even when the sound plays its full length. The result will remain a failure and
be investigated from actual recorded data rather than silently treated as an A-return.

Completed: the recording passed waveform checks but the original-prefix return prediction
failed on both channels. See [results](sound3-trim-return-results.md) and
[the separate copy-based return](sound3-copy-return-control.md).
