# Copy the imported sample from Sound6 to Sound7

Restore **experiments/edited-imported-sound6-to7-copy-001/restore.wav**. This isolated
candidate inserts the imported Sound6 header `00000000ab44000005` as a nine-byte
reference under previously empty Sound7. It adds no sample codes or backing capacity.
Every Sound6 code, other sample, pattern and opaque setting remains unchanged.

This tests the copy behavior at the imported endpoint 17,579, rather than the earlier
30,912 endpoint. It is a research probe; public copy/deletion guards are unchanged.

1. Restore the complete WAV using the proven stereo receive path and established
   playback level. Receive uses **write + sound + record**.
2. Select **Pattern 1 / Sound 8 / TONE**, stopped and write off. Keep both knobs and
   other settings unchanged.
3. **Before auditioning or playing a pattern**, record a complete stereo backup at
   the established reduced levels, with one second of trailing silence. Save it as
   **experiments/edited-imported-sound6-to7-copy-001/capture.wav**.
4. After saving, compare **Sound 6/key 1** and **Sound 7/key 1**: both should play the
   same rising pitch sweep for about 0.75 seconds. Sound4, Sound5 and Pattern1 should
   sound unchanged. Return to Sound8/TONE stopped and write off, and report whether
   the restore and all checks passed.

The registration pins the hardware-accepted source, target artifact, software report
and restore WAV before capture. Independent checks require the complete target body,
the exact Sound7 reference, unchanged Sound6 backing codes, only the expected two
owner5 referrers, unchanged patterns and unchanged non-Sound7 packets. Software checks
also reject stale-state and valid-checksum wrong-endpoint alternatives.

- [Software validation](../experiments/edited-imported-sound6-to7-copy-001/software-validation.json)
- [Restore registration](../experiments/edited-imported-sound6-to7-copy-001/restore-registration.json)
- Expected geometry: 952 packets, frame end byte 190,229
- Restore WAV SHA-256: `50d7a759036a91cfd00466ec8d6a77cfb5b3fa959867c140b663b3877dd93af9`
- Native body SHA-256: `0e9ea03263ec6060838e557ccfc568a90eb3cfc65c2dca7180095736abf72920`
- After decoding at the established threshold:
  `python -m scripts.check_sound6_to7_copy_restore --experiment-dir experiments/edited-imported-sound6-to7-copy-001 --artifact PATH_TO_NEW_CAPTURE_ARTIFACT`

Software reports remain `hardware_verified:false`; the manual restore and genuine
recapture must establish this new copy context separately.

## Completed

This copy is now hardware verified with the exact reference, complete backing codes
and full native body preserved. See [results](imported-sound6-to7-copy-results.md).
The public copy guard now includes this exact header. The next
[physical deletion control](imported-shared-sound6-deletion-control.md) checks shared
ownership transfer; its prediction is registered without requiring another restore.
