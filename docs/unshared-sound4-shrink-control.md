# Re-record the unshared Sound4 with a shorter tone

Sound4 now independently owns73728 codes/end72128; Sound5 independently owns the retained
32768-code/end28608 old sample. The verified owner3 reference list contains only Sound4.
Keep Sound5 and every pattern note present, with both knobs, effects, tempo and chain
unchanged.

The ordinary input is **experiments/calibration-unshared-shrink-001/tone-1500hz-0p25s.wav**:
a quarter-second1500Hz tone, stereo PCM16/44100Hz with identical channels, amplitude0.25
and short fades. SHA-256:
`6bebe496c813b3dce2b8b0793e0992322e153fa43600983f6f36d4699ec241fd`.

1. Keep **Pattern1**, playback stopped and **write off**. Connect computer output to
   the PO-33 line input with the successful sampling path and playback level.
2. Hold **record + keyboard key4**, play the complete quarter-second tone, then release
   after it ends. This re-records only Sound4. Keep Sound5 and both knobs unchanged.
3. Select **Sound8 / TONE**, playback stopped and write off. Reconnect the stereo backup
   recording path. **Before audition or pattern playback**, save a complete stereo
   PCM16/44100Hz dump at the successful reduced levels as
   **experiments/event-025-b-rerecord-unshared-sound4-short/capture.wav**. Let it finish
   completely and retain a second of trailing silence.
4. After saving, audition **Sound4/key1** for a brief changed tone and **Sound5/key1**
   for the retained old short tone, with write off. Return to Sound8/TONE, stopped/write
   off, and report both outcomes or deviations. Leave both sounds present.

Sampling follows the [official guide](https://teenage.engineering/guides/po-33/en).
Manual timing is not treated as an exact sample-length measurement.

Core checks pin the exact current buffer/header hashes, independently owned Sound5,
unshared owner3 reference list, pattern hashes and selector order. A changed/populated
Sound4 record and a complete checksum-valid frame are required; patterns stay identical.

Separate hypotheses test changed source codes, a smaller endpoint, smaller capacity
versus reuse of the original73728 capacity, owner3/zero-start retention, full Sound5
header/code preservation and all other sound/plain-packet preservation. Divisibility by
4096 versus8192 is reported independently: observed packet pages do not establish the
minimum allocation unit. No exact new capacity, endpoint, packet count or audible
duration is predicted from the input. Unknown owner/window layouts are reported without
guessed extraction. No allocator/resizing writer is enabled in advance.

- [Preregistered predictions](../experiments/unshared-sound4-shrink-predictions-001.json)
- [Experiment metadata](../experiments/event-025-b-rerecord-unshared-sound4-short/experiment.json)
- [Tone metadata](../experiments/calibration-unshared-shrink-001/source.json)
- [Validated shared-owner overwrite](shared-sound4-rerecord-results.md)
- Baseline WAV SHA-256: `5dca9a554b76bb538cf6a24deb5fdc707893730f6bea5519c76f5106342cb057`
- Baseline body SHA-256: `be92460f9d8014d92b54c1e6baf2a6fcdb29c8cad37a2f1d6f25cda3e69364b2`
