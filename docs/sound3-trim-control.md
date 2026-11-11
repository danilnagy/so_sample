# Locate Sound3 trim metadata

The current before-state is the Sound3-copy capture: sounds1/2/3/8 populated,
Sound8 selected, Pattern1 empty, write off and sequencer stopped. Keep the existing
capture level, master volume and other settings.

1. Select **Sound3** with **sound + 3**, then release.
2. Press **FX** until **tri** (TRIM) appears. Turn **knob B fully counterclockwise**
   to set Sound3's length to its minimum. Leave knob A untouched.
3. Press **FX** until **TONE** appears again, then reselect **Sound8**. Keep write
   mode off, Pattern1 empty and playback stopped; leave the knobs in place.
4. Record one full stereo backup as
   **experiments/empty-001-f-sound3-trim-min/capture.wav**.

The [official guide](https://teenage.engineering/guides/po-33/en) specifies FX mode
selection and knob B as sound length in TRIM. One capture suffices using the existing
Sound3-copy backup as the before-state. Leave the sounds present after capture.
Report deviations or a different starting FX mode; the expected starting mode is TONE
following the cleared-state protocol and subsequent copies. That starting mode was not
independently observed. This control explicitly returns FX mode/selection before capture.

The purpose is to test a parameter change rather than another populated destination.
The inline hypothesis predicts its first effect within the candidate Sound3 record,
preserving the main shared region and the same last-nonzero-increment boundary.
It is possible that trim settings serialize elsewhere, are omitted, or affect content
ownership. Failed predictions are retained and do not authorize a native-field patch.
Predictions are pinned in ../experiments/sound3-trim-predictions-001.json before upload.

Completed: the supplied capture passes the saved location, growth, boundary and anchor
checks. See [results](sound3-trim-results.md) and
[the return control](sound3-trim-return-control.md).
