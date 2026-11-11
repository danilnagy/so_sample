# Delete only shared owner Sound6 while retaining Sound7

The verified current backup contains self-owned Sound6, selector5, with32768 codes
and a0/30912/owner5 header. Sound7, selector6, holds only the identical nine-byte
reference to owner5. Both sounds play the same lower500Hz tone, about1.32seconds.
All source recordings, generated backups and exact hardware acceptance are preserved.

This is a physical device control, using the selected-sound deletion operation from
the [official guide](https://teenage.engineering/guides/po-33/en), already used in the
earlier clean-copy controls. Keep every other sound, pattern note, both knobs and
all other settings unchanged.

1. Keep **Pattern1**, playback stopped and write off. Select **Sound6** using
   **sound + keyboard key6**, then release both buttons.
2. Hold **record** and press **sound** to delete only the selected Sound6. Retain Sound7.
3. Select **Sound8 / TONE**, playback stopped, write off. **Before audition or pattern
   playback**, save a complete stereo backup at the successful reduced recording
   levels as **experiments/event-026-b-delete-shared-sound6/capture.wav**, including
   a second of trailing silence.
4. After saving, check **Sound6/key1** is empty/silent and **Sound7/key1** retains the
   same lower tone/duration. Check Sound4/key1, Sound5/key1 and Pattern1 sound unchanged.
   Return to Sound8/TONE stopped/write off and report all checks or deviations.

The preregistration pins the exact baseline WAV/artifact/native body, full Sound6
payload, Sound7 reference, owner5 referrers and every pattern hash. Core checks require
a valid changed state with preserved selectors/patterns, without forcing an ownership
or copy-preservation result. All other preservation claims are tested independently.

The primary full-transfer model predicts empty selector5 and a self-owned Sound7
record under selector6 with header `00000000c078000006`, all32768 original codes,
including the tail, and the same logical window. If all other packets remain unchanged,
geometry becomes951 packets/end190215: one fewer packet and14 fewer native-body bytes.
The entire predicted body is pinned as a comparison hypothesis before the capture.

An alternative keeps Sound7's reference to owner5 with full backing codes still stored
under Sound6, possibly with a changed source window. Both outcomes are evaluated
separately. Used-window preservation is also separate from full-buffer preservation:
tail corruption must not be accepted as an exact transfer. A lost Sound7 copy is
reported as a failed preservation hypothesis; missing or unknown owner/window layouts
are reported without guessed decoding. No predicted state guides acquisition or
native checksum verification, and no deletion writer is enabled before physical evidence.

- [Preregistered models](../experiments/shared-sound6-deletion-predictions-001.json)
- [Experiment metadata](../experiments/event-026-b-delete-shared-sound6/experiment.json)
- [Workflow audit](../experiments/shared-copy-to-sound6-deletion-workflow-validation-001.json)
- After normal capture decoding: `python -m scripts.check_shared_sound6_deletion`
- Full-transfer model body SHA-256: `15122b45a12cbe4ceab6ad4f5c5f7c5980f41ef772a9ed10ba7350e29edac4f1`

The control is awaiting a device capture. General deletion, allocation rounding and
mutating shared buffers remain unsupported.

The capture now matches the full-transfer model exactly, including every sample/tail
code and all unrelated packets. See [deletion results](shared-sound6-deletion-results.md).
The next control deletes the [now-unshared Sound7](unshared-sound7-deletion-control.md).
