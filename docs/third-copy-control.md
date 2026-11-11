# One further copy to test record spacing

The current clean-b capture is the before-state: Sound1, Sound2 and Sound8 populated,
Pattern1 empty, Sound8 selected, write mode off, playback stopped. Retain all of these
sounds and the existing knobs/recording settings.

1. Select Sound8 with **sound + 8**, then release.
2. Hold **write + sound**, press **3**, then release. This copies Sound8 into Sound3,
   which has remained empty in this series.
3. Reselect **Sound8**. Keep Pattern1 empty, write off, playback stopped.
4. Record one complete stereo backup as
   **experiments/empty-001-e-copy-to-3/capture.wav**.

These are the select/copy operations in the
[official guide](https://teenage.engineering/guides/po-33/en). The current clean-b
recording supplies the before-state, so one new capture suffices. Report any deviation,
including if Sound3 was already populated. Leave slots1/2/3/8 populated afterward.

The purpose is to test a specific transport-record hypothesis without recording fresh
audio:12 positions for an empty record,40 for a populated reference, difference28.
These proposed sizes are not decoded native fields. third-copy-predictions-001.json
pins the before artifact, first-change window, reference-prefix hashes, anchors,
complete-count allowance and exact last-nonzero-increment prediction before upload.
The constant carrier section is tracked separately. Failed predictions will remain
failed; no alignment, tail trimming or revised windows will rescue them.

Completed: the Sound3 capture passed the registered inline spacing, transition-boundary
growth and unchanged-anchor checks. See [results](third-copy-results.md) and
[the next parameter control](sound3-trim-control.md).
