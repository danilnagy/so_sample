# Delete Sound6 while Sound7 retains the imported sample

Use the current hardware-verified copied state. **No restore WAV is needed.** Delete
only Sound6 on the device, leaving Sound7 intact. The prediction is that all 32,768
backing codes move into Sound7 under owner6, preserving the exact 17,579 endpoint
and every tail code; Sound6 becomes empty.

1. Stop playback and turn write off. Select **Sound6** with **sound + 6**, then release
   both buttons. With Sound6 selected, **hold record and press sound** to delete it.
   Do not delete Sound7 or move either knob.
2. Return to **Pattern 1 / Sound 8 / TONE**, stopped and write off.
3. **Before auditioning or pattern playback**, record a complete stereo backup at the
   established reduced levels, with one second of trailing silence. Save it as
   **experiments/event-028-b-delete-imported-shared-sound6/capture.wav**.
4. After saving, check **Sound 6/key 1 is silent** and **Sound 7/key 1 still plays the
   same rising sweep for about 0.75 seconds**. Sound4, Sound5 and Pattern1 should sound
   unchanged. Return to Sound8/TONE stopped and write off, and report the checks.

The registration pins the exact accepted copied-state source and predicted native
body before the control. The checker separates valid changed-state controls from
ownership hypotheses: empty Sound6, full self-owned Sound7, exact codes and logical
window, unrelated-packet preservation, geometry and complete model equality.
Retaining owner5 or a dangling Sound7 reference are explicit alternatives. A changed
endpoint does not by itself imply loss of sample codes.

Software tests reject a stale copied state, clearing the owner while leaving a
dangling reference, and altering an unused tail code even if the audible window
remains exact. Public deletion guards have not been extended to this new endpoint.
The predicted body is evidence of a model, not a hardware result or device action.

- [Deletion registration](../experiments/event-028-b-delete-imported-shared-sound6/deletion-registration.json)
- [Software prediction checks](../experiments/event-028-b-delete-imported-shared-sound6/software-prediction-validation.json)
- Prediction: 951 packets, frame end byte 190,215, 14 fewer native body bytes
- Predicted Sound7 header: `00000000ab44000006`
- Predicted body SHA-256: `684437bc68251bb2cf3400e64be024d677baeb0e5389106c0122ea30b30724f1`
- After decoding the new capture: `python -m scripts.check_imported_shared_deletion`

## Completed

The physical transfer now exactly matches the registered native body. See
[results](imported-shared-sound6-deletion-results.md). The shared-deletion writer now
includes the verified imported endpoint. The next
[last-owner control](imported-unshared-sound7-deletion-control.md) requires deleting
only Sound7 and capturing before audition; no restore is needed.
