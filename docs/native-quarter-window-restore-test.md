# Test the window at the second start

Completed: the clean retry matches the entire generated target with511 valid checksums,
and the user confirms restore and both tone checks. See
[second-start hardware results](native-quarter-window-results.md) and the
[next drum control](drum9-copy-control.md). The retry was uploaded over `capture.wav`
and preserved as `capture-retry.wav`; the first failed WAV was replaced by the user,
while its artifact and diagnostic reports remain. Earlier instructions and failure status follow.

The user reports **"done and passed"** for restore and both tone checks. The first
recapture cannot yet verify the target: the crossing decoder fails at the first packet,
and measured-clock recovery lacks an exact pre-frame alignment. Waveform-only diagnostics
find widespread quarter-relation errors, compared with zero in the previous clean control.
The original recording and failed attempts are preserved. See
[verification status](../experiments/edited-quarter-window-001/capture-verification-status-001.json).

**Next action:** retain the current device state, with both knobs untouched. Record another
full stereo backup using the previous successful input path and recording settings as
**experiments/edited-quarter-window-001/capture-retry.wav**. Keep Sound8/TONE selected,
write off and playback stopped. No additional restore or audition is needed. Use stereo
PCM16/44100Hz without effects and preserve the original capture. The
[retry registration](../experiments/edited-quarter-window-001/recapture-retry-registration.json)
retains the exact expected target; auditions may have changed unrelated state, which will
be reported if present. Higher recorded peaks alone do not prove clipping or its cause.

Original restore instructions follow.

Restore **experiments/generated-quarter-window-001/restore-sound3-quarter-window.wav**
with the proven stereo playback path and levels. Enter receive with **write + sound + record**
and play the entire stereo PCM16/44.1kHz transfer, approximately23.1seconds.

1. Confirm that restore succeeds. Keep both knobs untouched.
2. **Before audition or pattern playback**, select **Sound8 / TONE**, with write off
   and playback stopped. Save a complete stereo backup with the existing recording
   settings as **experiments/edited-quarter-window-001/capture.wav**.
3. After saving, select **Sound3 / TONE** with write off and tap **keyboard key1**.
   Confirm a clearly audible brief tone. Its8000-code window should sound similar in
   duration to the previous successful window, roughly a quarter second at key1;
   this is a prediction rather than a measured hardware duration.
4. Select **Sound8 / TONE** and tap keyboard key1. Confirm its longer tone remains
   unchanged, then leave Sound8 selected with playback stopped.

The candidate keeps start**11716** and changes endpoint**11827→19716**, reference
**c42d0000044d000000**. Only reference packet375 bytes4/5 change; backing codes,
other sound records, patterns and unrelated native packets stay identical.

- [Software validation](../experiments/generated-quarter-window-001/software-validation.json)
- [Registered target](../experiments/edited-quarter-window-001/restore-registration.json)
- WAV SHA-256: `a81d6bb2e2eb9532155d00355933d0eabb9d2e8a1bb92c45a6b50f8249d7db2a`
- Expected body SHA-256: `933eca1c290f4fcde0718ddf87e342c3f5b059bbb96d070f98fd6145c342699a`
- The genuine pre-test backup remains in `experiments/event-014-b-sound3-start-quarter/capture.wav`.

**window-preview-48k.wav** is an unpitched mono preview, not a data transfer. It reads
raw codes[11716:19716], resampled to16384FLOAT frames at48kHz. This explicit half-open
preview convention does not resolve exact device endpoint inclusivity.

Reproduce in a fresh directory:

```powershell
.\.venv\Scripts\python.exe -m scripts.make_quarter_window_candidate --out-dir experiments/generated-quarter-window-002
```

The regular editor remains limited to the previous start31393 until this independent
second-start candidate passes a device restore, exact recapture and audition test.
