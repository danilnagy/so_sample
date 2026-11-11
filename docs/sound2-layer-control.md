# Add a second sound to one step

Completed: every preservation and cell-location check passes. Sound 2 primary
**0d2831** differs from predicted **0df883**, so that hypothesis fails; auxiliary
F0 matches. See [Sound 2 results](sound2-layer-results.md). The original protocol
below is retained for provenance.

Keep the current four-key Pattern 1. Its Sound 3 notes at Steps 1/5/9/13 are the
verified baseline. Sound 2 contains the same shared tone with its original longer
trim; its Pattern 1 cells are empty. Only one new backup is required.

1. Stop playback and leave write mode off. Retain **Pattern 1** and select **Sound 2**.
2. With write **off**, tap **keyboard key 1** once to select its pitch.
3. Press **write**. Sound 2's **Step 1 should be unlit**. Tap **Step 1 once** to add
   its note, then press **write** again to exit. Keep every Sound 3 note in place.
4. Reselect **Sound 8**, retain **TONE**, keep playback stopped and all knobs,
   effects, tempo, pattern chain and recording settings unchanged. Record a complete
   stereo backup **before playing the changed pattern**, as
   **experiments/event-011-b-sound2-layer/capture.wav**.

If Sound 2's Step 1 is already lit, exit write without tapping it and report that
state. Leave the newly added note in place after recording. No pattern playback or
second restore is needed for this control. Controls follow the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en).

The registered locality prediction permits changes only in **primary bytes [3,6)**
and **auxiliary byte 769**, the candidate Sound 2 cell on Step 1. All four existing
Sound 3 notes, samples, other patterns, footer and unrelated packets must remain
unchanged. Step 1 should then contain cells for Sounds 2 and 3. The baseline's
Sound 2 target cell is independently checked to be empty before registration.

Separate raw-value hypotheses predict primary `0df883` and auxiliary `F0`, extending
the observed Sound 3 key 1 values to Sound 2. These are unverified predictions, not
conditions that can turn an unexpected value into a successful mapping. Report
locality/preservation and hypothesis fits separately. No Sound 2 or multi-sound writer
is enabled yet, and this control does not prove audible polyphony.

The baseline is **edited-four-keys-001**, using its verified **analysis-002**
measured-clock artifact, not the failed analysis-001 crossing artifact.

- Source WAV SHA-256: `2cc8b8df219f49e9a0721d67ecf719c37575f9f9da7f264eac5b2c4736eb84bf`
- Body SHA-256: `9b87309f572b188cd1e1a2651b1ca4feec5cfa8fb669068631042ca8f49465f0`
- Artifact SHA-256: `853f5ea6670d5b4508190f79d5547453ea9119fa95c98dc06cd02f1e5861d0b0`
- [Registered predictions](../experiments/sound2-layer-predictions-001.json)
- [Experiment metadata](../experiments/event-011-b-sound2-layer/experiment.json)

Measured-clock recovery, if needed, must use waveform data and pre-frame alignment
without the expected note values or a target frame.
