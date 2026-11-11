# Delete the last imported sample owner in Sound7

Use the current verified state with Sound6 empty and the imported sweep owned by
Sound7. **No restore is needed.** Delete only Sound7. The registered prediction removes
its complete record, yielding the exact earlier genuine backup with both slots empty.

1. Stop playback and turn write off. Select **Sound7** with **sound + 7**, then release
   both buttons. With Sound7 selected, **hold record and press sound** to delete it.
   Keep both knobs and all other sounds/settings unchanged.
2. Return to **Pattern 1 / Sound 8 / TONE**, stopped and write off.
3. **Before auditioning or playing a pattern**, record a complete stereo backup at the
   established reduced levels, with one second of trailing silence. Save it as
   **experiments/event-029-b-delete-imported-unshared-sound7/capture.wav**.
4. After saving, confirm **Sound 6/key 1 and Sound 7/key 1 are both silent**. Sound4,
   Sound5 and Pattern1 should sound unchanged. Return to Sound8/TONE stopped and write
   off, and report the checks.

The removal model already equals the complete independently verified native body from
`event-027-b-delete-unshared-sound7`. That earlier genuine capture and result are pinned
by hash. The checker separates empty-record removal from retained backing codes and
changed metadata, while independently checking all unrelated packets and patterns.

Software tests reject the stale transferred state and a retained full buffer with
changed endpoint. The public Sound7 deletion guard has not been extended to endpoint
17,579 in advance. Serialized record removal does not measure physical RAM reclamation.

- [Deletion registration](../experiments/event-029-b-delete-imported-unshared-sound7/deletion-registration.json)
- [Software prediction checks](../experiments/event-029-b-delete-imported-unshared-sound7/software-prediction-validation.json)
- Prediction: 815 packets, frame end byte 156,758; 136 data packets and 33,457 native
  body bytes removed, with Sound6/Sound7 both empty
- Predicted body SHA-256: `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0`
- After decoding the new capture:
  `python -m scripts.check_unshared_sound7_deletion --experiment-dir experiments/event-029-b-delete-imported-unshared-sound7 --artifact PATH_TO_NEW_CAPTURE_ARTIFACT`

## Completed

The physical capture exactly matches the independently genuine earlier empty-slot
state. See [results](imported-unshared-sound7-deletion-results.md). Both imported
deletion contexts are now supported within their existing bounded guards. The next
[tempo control](tempo-preset-control.md) uses one BPM button press, with both knobs
unchanged, and requires the displayed BPM before and after.
