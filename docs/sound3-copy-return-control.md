# Return by copying the retained source

Maximum trim length produced a valid capture but did not match the original untrimmed
Sound3 state. Use the retained Sound8 as the source for this separate return hypothesis.

1. Select **Sound8** with **sound + 8**, then release.
2. Hold **write + sound**, press **3**, then release. This copies over the current Sound3.
3. Reselect **Sound8**; retain **TONE**, empty Pattern1, write mode off, playback stopped,
   and unchanged knobs, master volume and capture settings.
4. Record one full stereo backup as
   **experiments/empty-001-h-sound3-copy-return/capture.wav**.

The [official guide](https://teenage.engineering/guides/po-33/en) specifies copying the
selected sound using write+sound and the destination key. Leave sounds1/2/3/8 present
afterward and report deviations. One capture uses the saved maximum-length state as
the before-state.

Predictions in ../experiments/sound3-copy-return-predictions-001.json pin both that before
artifact and the original Sound3-copy reference. The original prefix[0,178795) must match
exactly on both channels; complete-array/count equality and partial intervals are separate.
No shifted or phase-corrected comparison can count as a return.

This tests whether copying replaces the relevant destination settings with the retained
source's values. If it preserves destination settings or the source itself changed,
the predicted return may fail. The earlier maximum-knob return remains failed regardless
of this experiment's outcome.

Completed: copying over Sound3 matches all complete labels and both counts of the
original reference. See [results](sound3-copy-return-results.md) and
[the ordinary-playback control](minimal-tone-playback-control.md).
