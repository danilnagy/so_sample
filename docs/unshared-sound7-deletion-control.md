# Delete the now-unshared Sound7 sample

Sound6 is empty. Sound7 independently owns32768 sample codes, with header
`00000000c078000006` (start0/end30912/owner6). The current raw reference list to owner6
contains only selector6. Sound4, Sound5 and every pattern remain as previously checked.

1. Keep **Pattern1**, playback stopped and write off. Select **Sound7** with
   **sound + keyboard key7**, then release both buttons.
2. Hold **record** and press **sound** to delete only Sound7. Keep both knobs and all
   other sounds/notes/settings unchanged.
3. Select **Sound8 / TONE**, stopped/write off. **Before audition or pattern playback**,
   save a complete stereo backup at the successful reduced levels as
   **experiments/event-027-b-delete-unshared-sound7/capture.wav**, including a second
   of trailing silence.
4. After saving, check **Sound6/key1** and **Sound7/key1** are empty/silent. Sound4/key1,
   Sound5/key1 and Pattern1 should sound unchanged. Return to Sound8/TONE stopped/write
   off and report the checks or deviations.

This is the same selected-sound deletion operation used previously and described in
the [official guide](https://teenage.engineering/guides/po-33/en). Existing backup files
and full buffer data remain preserved in the workspace.

The preregistration pins the exact current WAV/artifact/native body, full Sound7
payload, unshared owner6 reference list and every pattern hash. Core checks require
a valid changed state and preserved selectors/patterns. Empty Sound7, preserved empty
Sound6, retained full codes under owner6 and all unrelated-record preservation are
evaluated separately, without forcing removal as the result.

The empty-record model removes136 data packets/33457 encoded-body bytes, predicting
815 packets/end156758 and complete body `12acce04...`. Independently, this predicted
body equals the earlier genuine hardware shrink backup from before Sound6 creation.
That prior state provides an external comparison to the packet-removal model.
The expected serialized code capacity drops32768 bytes; this is not a measurement
of physical RAM reclamation. A zero endpoint with retained full codes must not be
reported as removal. No predicted state guides acquisition or checksum verification.

- [Preregistered models](../experiments/unshared-sound7-deletion-predictions-001.json)
- [Experiment metadata](../experiments/event-027-b-delete-unshared-sound7/experiment.json)
- After normal capture decoding: `python -m scripts.check_unshared_sound7_deletion`
- Expected empty-record body SHA-256: `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0`

This physical control is pending. No generated deletion operation or general allocator
is enabled; the verified Sound6-to7 copy is separately available through bounded edit plans.

The capture now removes the full Sound7 record and matches the complete earlier
pre-creation state. See [results](unshared-sound7-deletion-results.md). The bounded
deletion edit-plan operations replay the observed states; the next device test concerns
[nine-page serialized capacity](sound6-nine-page-control.md).
