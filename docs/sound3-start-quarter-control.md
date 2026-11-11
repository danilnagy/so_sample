# Check a second sample-start position

Completed: all preservation checks pass, with start11716 and endpoint11827. The lower
start prediction passes and both endpoint predictions fail. See
[second-start results](sound3-start-quarter-results.md) and the
[next restore test](native-quarter-window-restore-test.md). Original instructions follow.

The current hardware-verified Sound 3 window has start31393, endpoint39393 and owner0.
We need a second independently created start value before broadening the writer beyond
its current fixed-start calibration. One new backup is sufficient.

1. Keep **Pattern 1**, playback stopped and write off. Select **Sound 3**.
2. Select **TRIM / tri** with FX. Turn **only knob A** fully counterclockwise, then
   bring it to approximately **one quarter of its travel**. **Leave knob B untouched**.
3. Return to **TONE**, select **Sound 8**, and retain all other settings. Record a
   complete stereo backup **before audition or pattern playback** as
   **experiments/event-014-b-sound3-start-quarter/capture.wav**.

Leave the changed start in place afterward. The
[official guide](https://teenage.engineering/guides/po-33/en) assigns knob A to start in TRIM mode.

Preservation checks permit changes only in the first eight bytes of the existing Sound 3
reference packet. Ownership, backing codes, other sounds, every pattern and unrelated
packets must remain identical. The second field may move with knob A, as observed in
the first start control; that change is reported explicitly and never masked.

Separate hypotheses predict a positive first value below31393 and either unchanged
second39393 or reset second65535. No exact first value is predicted from an approximate
knob position. Other second values remain unclassified. Physical knob B still has its
previous position, which differs from the generated endpoint; possible coupling remains
under investigation. No broader start or minimum-width rule is enabled by registration.

- [Preregistration](../experiments/sound3-start-quarter-predictions-001.json)
- Baseline WAV SHA-256: `7935f7cfe3ab7a8b8d45dbe942f3144dad2c7eebb09c8aa52fb06f96a1d632d8`
- Baseline body SHA-256: `b3296f2ed7b3a74cedc79b8d89900e5128c7da1da0e2fed9839d1858412eddfe`

Measured-clock recovery, if needed, must not use expected header values or target packets.
