# Re-record Sound4 while retaining its shared Sound5 copy

Completed:985 native checksums pass. Sound4 grows to73728 codes, while the complete
original32768-code buffer transfers to self-owned Sound5/owner4, unchanged byte for byte.
All unrelated state remains intact. See [results](shared-sound4-rerecord-results.md)
and the [next unshared shrink control](unshared-sound4-shrink-control.md). Original
registration and instructions follow unchanged.

Sound4 owns the32768-code1kHz buffer; Sound5 is a reference to its start0/end28608
window. Keep Sound5 present, every existing pattern note, both knobs, effects, tempo
and pattern chain unchanged.

The prepared ordinary input is
**experiments/calibration-shared-overwrite-001/tone-1250hz-2s.wav**: two seconds at
1250Hz, stereo PCM16/44100Hz with identical channels, amplitude0.25 and short fades.
Its SHA-256 is `94853f1452fbef12fe4f8e99e33458d7f9f8b63fec65a308f5ddae8c5d438e08`.
The longer duration and distinct frequency make allocation growth and retained-copy
behavior distinguishable from the old sample; manual gating is not an exact measurement.

1. Keep **Pattern1**, playback stopped and **write off**. Connect the computer output
   to the PO-33 line input using the successful sampling path and playback level.
2. Hold **record + keyboard key4**, play the **entire two-second tone**, then release
   after it ends. This replaces only Sound4. Leave Sound5 present and avoid copying or
   deleting another sound. Keep both knobs untouched.
3. Select **Sound8 / TONE**, playback stopped and write off. Reconnect the proven
   stereo backup path. **Before audition or pattern playback**, record a full stereo
   PCM16/44100Hz dump at the same reduced input levels as
   **experiments/event-024-b-rerecord-shared-sound4/capture.wav**. Let the entire dump
   finish; it may be longer. Retain a second of trailing silence.
4. After saving, with write off, audition **Sound4/key1** and **Sound5/key1**. Report
   whether Sound4 is longer/different, and whether Sound5 retains the previous short
   tone, changes with Sound4 or is silent. Return to Sound8/TONE, playback stopped and
   write off. Leave both sounds present and report any early stop or deviation.

Line-input sampling follows the
[official guide](https://teenage.engineering/guides/po-33/en). The new sample is
ordinary audio to record, using the established sampling workflow.

Core checks require the exact registered before-state, a changed/populated Sound4
record, unchanged patterns and selector order, and a complete checksum-valid frame.
Actual owner records, buffer sizes, endpoints, packet counts and all changed sounds are
reported. Unexpected Sound5 loss or allocator/global bookkeeping remains visible and is
not forced into a preservation result.

Separate hypotheses test zero-start/different/grown Sound4 data, a retained Sound5
record and unchanged logical Sound5 sample window, full transfer of the original32768
codes into a self-owned Sound5/owner4 buffer, versus an unchanged Sound5 reference that
tracks the new Sound4 codes. Transfer of the full buffer is narrower than preservation
of the used sample window. Exact original owner0 and unrelated-record/non-Sound4/5
packet preservation are also evaluated independently.

Raw window comparisons use the existing zero-start endpoint convention. Unknown or
nonzero-start backing layouts are reported without guessed extraction. No exact new
capacity, endpoint, native length or rounding rule is assumed from the two-second input.
No allocator, resizing or shared-owner overwrite writer is enabled in advance.

- [Preregistered predictions](../experiments/shared-sound4-rerecord-predictions-001.json)
- [Experiment metadata](../experiments/event-024-b-rerecord-shared-sound4/experiment.json)
- [Tone metadata](../experiments/calibration-shared-overwrite-001/source.json)
- [Verified shared-reference baseline](sound4-to5-copy-results.md)
- Baseline WAV SHA-256: `9cf4096737c90537a7dacbb0d4f4436c8730958468a7313eee97e73d5ed0c387`
- Baseline body SHA-256: `eb19589f3bf193f81611a7322bf79c98881531f24269eed2b8c67e342d731dfb`
- Baseline artifact is **analysis003 at threshold0.004**, corroborated by two additional
  fixed profiles. The failed analysis001 acquisition is not the source state.
