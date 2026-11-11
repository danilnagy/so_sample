# Change one recorded melodic key

Completed: all control invariants and both separately registered hypotheses pass.
Exactly auxiliary byte834 changes F0→F1; primary note bytes, samples and the other
three notes are unchanged. See [key2 results](melodic-key2-results.md).
The instructions below are retained as the completed physical control protocol.

The four-note pattern is now hardware validated: the user reports expected playback,
and its backup matches the generated native body exactly. The backup was explicitly
recorded **after playback**, with no playback-induced native differences. It is the
baseline for this next control; no new baseline recording is needed.

Change **Pattern1, Step5, Sound3** from **melodic keyboard key1 to key2**:

1. Keep playback stopped and write mode off. Select **Sound3** with sound+3, retaining
   Pattern1. Press **write**, tap **Step5 once** to remove its existing note, confirm
   that Step5's light goes off, then press **write** again to exit.
2. With write mode **off**, tap **key2** once to select/audition that melodic note.
   Press **write**, tap **Step5 once** to add it, then press **write** again to exit.
3. Reselect **Sound8**. Keep TONE, playback stopped, unchanged knobs, effects, tempo,
   chain and recording settings. Record the complete stereo backup **before playing
   the changed pattern**, as **experiments/event-008-b-melodic-key2/capture.wav**.

Leave the replacement note in place. Steps1/9/13 should retain their original notes.
If the Step5 light does not match the expected remove/add state, report what happened.
Do not make additional edits to compensate before recording the action history.

Keyboard key2 is selected outside write mode; Step5 is edited inside write mode. This
separates note choice from step position. Controls follow the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en), sections3/4/5/8.

The source WAV SHA-256 is
`494957d160d0454eef3db5273e05496c59f98b6da89c0dc6bb25ee9115c182af`.
Its native body SHA-256 is
`8b39765df9a4caf71e509f54b0c49e2f0d95ad1a60f4effa46daa687259d0104`.
Expected packet count is511 and native frame end89396. Samples, other patterns and
all Pattern1 cells outside Sound3 Step5 should remain unchanged.

We predict, separately from those control invariants, that Sound3's three primary bytes
at[198,201) remain `0df883`, while auxiliary byte834 changes fromF0 toF1. The hypothesis
is that the low nibble stores keyboard index0..15; the upper nibble remains opaque.
This is **not yet a decoded or writable note field**. A missed hypothesis must be
retained even if all control checks pass. See
[registered predictions](../experiments/melodic-key2-predictions-001.json).
