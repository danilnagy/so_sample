# Test the fixed-start sample window

Completed: the user confirms both tone checks. The recapture matches the complete target
with all511 checksums valid and samples/patterns preserved. See
[fixed-start hardware results](native-nonzero-trim-results.md). Original instructions are retained below.

Restore **experiments/generated-nonzero-trim-001/restore-sound3-window.wav** using
the proven stereo playback path and levels. Enter receive with **write + sound + record**
and play the entire 44.1 kHz stereo PCM16 transfer, approximately 23.1 seconds.

1. Report whether restore succeeds.
2. **Before audition or pattern playback**, select **Sound 8 / TONE**, with write off
   and playback stopped. Save a full stereo backup with the existing recording settings
   as **experiments/edited-nonzero-trim-001/capture.wav**.
3. After saving, select **Sound 3** with write off and tap **keyboard key 1**. Confirm
   a clearly audible brief tone instead of the previous minimum click. Roughly a quarter
   second is the local prediction from the 8000-code window and earlier key 1 calibration;
   it is not an independently measured duration for this candidate.
4. Select **Sound 8** and tap keyboard key 1. Confirm its longer tone is unchanged.
   Return to **Sound 8 / TONE** and leave playback stopped afterward.

The Sound 3 start stays **31393**. Only the endpoint changes **31504 to 39393**,
giving raw reference **a17a0000e199000000**. Only bytes 4/5 in plain packet 375 change.
All backing codes, other sound headers, ownership and all sixteen patterns are preserved.

- [Software validation](../experiments/generated-nonzero-trim-001/software-validation.json)
- WAV SHA-256: `06b311337489a1176c80bc27172b343dc649ec2bd4c6880ad0d967470527949f`
- Expected body SHA-256: `b3296f2ed7b3a74cedc79b8d89900e5128c7da1da0e2fed9839d1858412eddfe`
- Exactly 511 packets, frame end 89396. Full phase/count waveform roundtrip and exact
  native target recovery pass. The genuine larger and minimum endpoint bodies and inverses
  are reproduced exactly by the writer.

**window-preview-48k.wav** in the same candidate folder is an unpitched mono sample
preview, not a data transfer. It contains 16384 float samples at 48 kHz, using an explicit
half-open selection of 8000 raw codes at the nominal 23437.5 Hz rate. Exact device endpoint
inclusivity and a general minimum-width rule remain unresolved. The failed exact minimum
predictions are retained in the original control report.

The existing minimum backup is preserved in **experiments/event-013-b-sound3-start-min/capture.wav**.
Its separate hardware result is now recorded in the completed results above.
Controls follow the [official PO-33 guide](https://teenage.engineering/guides/po-33/en).

Reproduce in a fresh directory:

```powershell
.\.venv\Scripts\python.exe scripts/make_nonzero_trim_candidate.py experiments/event-013-b-sound3-start-min/derived/analysis-001/capture.symbols.npz --out-dir experiments/generated-nonzero-trim-002
```
