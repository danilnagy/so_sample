# Test a generated nonzero-start drum window

Completed: the clean retry matches the entire registered target with527 valid checksums,
and the user confirms restore and both Sound9 tones. See
[hardware results](native-drum9-key2-end-results.md) and the
[next Sound10 control](drum10-copy-control.md). The retry is preserved as `capture-retry.wav`;
the failed first WAV, artifact and diagnostics remain archived. Earlier failure status
and original instructions follow.

The user reports **"done and confirmed"** for restore and both Sound9 tone checks.
The first recapture cannot yet verify the target: normal crossing decode fails at the
first packet, measured-clock recovery lacks an exact pre-frame alignment, and fixed
higher thresholds also fail. Waveform-only diagnostics find363left/64right cells
violating the quarter-sign model at the best offsets, mostly after the pre-frame region.
This is not a reported device restore failure. The exact recording cause remains unknown,
and no digital clipping indicators are present. See
[verification status](../experiments/edited-drum9-key2-end-001/capture-verification-status-001.json).

**Next action:** retain the current device state and both knob positions. With Sound8/TONE,
write off and playback stopped, record another complete stereo backup using the previous
successful input path/settings as **experiments/edited-drum9-key2-end-001/capture-retry.wav**.
Use stereo PCM16/44100Hz without effects. No new restore or audition is needed. The first
WAV is archived as `capture-attempt-001.wav`, and all failed artifacts/diagnostics remain
preserved. [Retry registration](../experiments/edited-drum9-key2-end-001/recapture-retry-registration.json)
retains the exact target and accepted key1 reference. Subsequent state differences will be
reported if present. Original restore instructions follow.

Restore **experiments/generated-drum9-key2-end-001/restore.wav** through the proven
stereo playback path and levels. Enter receive with **write + sound + record**, then
play the entire stereo PCM16/44100Hz transfer, approximately23.16seconds.

1. Confirm restore succeeds. Keep both knobs untouched.
2. **Before audition or pattern playback**, select **Sound8 / TONE**, with write off
   and playback stopped. Save a complete stereo backup with the successful recording
   settings as **experiments/edited-drum9-key2-end-001/capture.wav**.
3. After saving, select **Sound9 / TONE**, write off, and tap **key2**. Confirm a clear
   short tone instead of the minimum click.
4. Tap **Sound9/key1** and confirm its previously accepted short tone is unchanged.
   Both2000-code windows should have similar duration; exact device rendering has not
   been independently measured. Reselect **Sound8 / TONE** afterward, write off and
   playback stopped. Report restore and both Sound9 tone checks.

The candidate changes only key2 endpoint4172→6045, retaining start4045, owner0 and
the accepted key1 reference `00000000d007000000`. Key2 becomes
**cd0f00009d17000000**. Only bytes4/5 of packet385 change; all other slices, backing
codes, melodic sounds, patterns and unrelated packets remain identical.

- [Software checks](../experiments/generated-drum9-key2-end-001/software-validation.json)
- [Registered target](../experiments/edited-drum9-key2-end-001/restore-registration.json)
- WAV SHA-256: `28d4cdd4363c081ac94bf5b1447ccb70b9d0672cb5519139bddee60ca979f2ab`
- Expected body SHA-256: `1f3295c4cc8150d75a1513c76d996c54ed460c9b9d26730c556d7da24065ad28`
- Exactly527 packets, frame end89620; strict software phase/count/body checks pass.
- Genuine minimum backup: `experiments/event-017-b-drum9-key2-trim-min/capture.wav`.

**slice-preview-48k.wav** is a standalone mono sample preview, not a data transfer.
It uses raw codes[4045:6045] under the explicit half-open policy, without pitch/gain
changes, producing4096FLOAT frames at48kHz. This preview policy does not resolve device
endpoint inclusivity. The first key1 edit's hardware acceptance does not establish
acceptance of this new nonzero-start edit.

Reproduce in a fresh folder:

```powershell
.\.venv\Scripts\python.exe -m scripts.make_drum_key2_candidate --plan experiments/drum9-key2-end-plan-001/plan.json --out-dir experiments/generated-drum9-key2-end-002
```

Scope remains the two observed fixed starts and their separate local intervals, owner0
and the literal other14 references. Arbitrary starts, other keys/drum slots, allocation
and universal minimum-width rules remain unsupported.
