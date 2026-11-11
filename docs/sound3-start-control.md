# Move only Sound 3's sample start

Completed: all preservation checks pass, and the user still hears the tone. The first
field moves to 31393 and the second becomes 65535, rejecting both registered second-field
predictions. See [start results](sound3-start-results.md). The original protocol below is retained.

Use the current verified removal state: Sound 2 only at Step 9; the four Sound 3
notes remain at Steps 1/5/9/13. Sound 3's reference is `00000000401f000000`:
the first four bytes are zero, the B-controlled second field is 8000 and owner ID is 0.
The shared backing buffer has 65,536 codes. The existing capture is the baseline,
so one new backup is sufficient.

1. Keep Pattern 1, playback stopped and write off. Select **Sound 3**.
2. Press **FX** until **TRIM / tri**. Turn **only knob A** fully counterclockwise,
   then bring it to approximately halfway through its travel. **Leave knob B untouched**
   and keep all other settings unchanged.
3. Return FX to **TONE**, reselect **Sound 8**, and keep write off / playback stopped.
   **Before auditioning or playing the pattern**, record a complete stereo backup as
   **experiments/event-012-b-sound3-start/capture.wav**.
4. After saving, select Sound 3 with write off and tap **keyboard key 1**. Report
   whether a short tone is still audible, or whether it is silent. Return to **Sound 8 / TONE**.

The [official PO-33 guide](https://teenage.engineering/guides/po-33/en), reviewed
2026-10-08, specifies knob A as sample start and knob B as length in TRIM mode.
Leave the changed start in place after recording and report any deviation.

The preregistered preservation checks allow changes only in the first eight bytes
of the existing nine-byte Sound 3 reference packet. All sample codes, ownership,
other sound records, every pattern cell and unrelated packets must stay identical.
The physical knob position does not supply an exact native byte prediction.

Separate hypotheses test a nonzero little-endian first field and two alternatives
for the second field: remaining 8000, or moving with the first field while retaining
a difference of 8000. The alternatives are not simultaneous requirements. If the
new first field remains below 8000 and the second field stays constant, this alone
cannot distinguish fixed endpoint from fixed length; further evidence would be needed.
No nonzero-start extractor or writer is enabled by this registration.

- [Registered hypotheses](../experiments/sound3-start-predictions-001.json)
- Baseline WAV SHA-256: `aa8c083704bb92aa44893bafc3abd35e2bc05182fbb01ca7511f04752dafeb7d`
- Baseline body SHA-256: `1e493f1495ecf2dc68077a35ae97b8883acbe96b94d0798427a9f3f990a1761a`

Measured-clock decoding, if needed, must not use these expected values or a target body.
