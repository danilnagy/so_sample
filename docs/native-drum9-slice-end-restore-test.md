# Test the first generated drum-slice edit

Completed: the user confirms restore and both tone checks, and the complete recapture
matches the registered target with527 valid checksums. See
[hardware results](native-drum9-slice-end-results.md) and the
[next key2 control](drum9-key2-trim-min-control.md). Original instructions follow.

Restore **experiments/generated-drum9-slice-end-001/restore.wav** through the proven
stereo playback path and levels. Enter receive using **write + sound + record** and play
the entire stereo PCM16/44100Hz transfer, approximately23.16seconds.

1. Confirm restore succeeds and keep both knobs untouched.
2. **Before audition or pattern playback**, select **Sound8 / TONE**, with write off and
   playback stopped. Record a complete backup using the successful settings as
   **experiments/edited-drum9-slice-end-001/capture.wav**.
3. After saving, select **Sound9 / TONE** with write off and tap **keyboard key1**.
   Confirm a clearly audible short tone. The2000-code unpitched preview lasts about85ms;
   exact device duration and playback parameter effects have not been measured.
4. Select **Sound8 / TONE** and tap keyboard key1. Confirm its longer tone remains
   unchanged. Leave Sound8 selected, write off and playback stopped.

Report restore and both tone checks. The candidate changes Sound9/key1 endpoint127→2000
while preserving start0, owner0 and the other15 slices. It changes only bytes4/5 of
packet383, producing reference **00000000d007000000**. All backing codes, melodic sounds,
patterns and unrelated packets remain identical.

- [Software validation](../experiments/generated-drum9-slice-end-001/software-validation.json)
- [Registered target](../experiments/edited-drum9-slice-end-001/restore-registration.json)
- WAV SHA-256: `76c74a4a3b10cbc8324b606adf7af4b901c29b333e2c4fcfe31fc9380e382c41`
- Expected native body SHA-256: `4eca78dcdf5521941bb07c0d16e4cad71115512021670c203d87256ce142e667`
- Exactly527 packets, frame end89620; all strict software checks pass.
- The genuine minimum backup remains in `experiments/event-016-b-drum9-key1-trim-min/capture.wav`.

**slice-preview-48k.wav** is a mono raw-sample preview, not a transfer. Its half-open
selection convention does not establish exact hardware endpoint inclusivity. The original
79 minimum prediction remains failed;127 is only the locally observed control value.

Reproduce in a fresh folder:

```powershell
.\.venv\Scripts\python.exe -m scripts.make_drum_slice_candidate --plan experiments/drum9-slice-end-plan-001/plan.json --out-dir experiments/generated-drum9-slice-end-002
```

No other drum keys, starts, sound slots, allocation or neighboring-boundary changes are
supported by this candidate. This first generated drum operation requires its own
hardware evidence even though the other sample/pattern writers have passed earlier tests.
