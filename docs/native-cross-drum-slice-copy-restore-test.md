# Test the generated nonzero-start cross-drum slice copy

Completed: the recapture exactly matches the entire target with543 valid checksums,
and the user confirms restore and all requested tone checks. See
[hardware results](native-cross-drum-slice-copy-results.md) and the
[next physical drum-note control](drum10-note-control.md). Original target registration
and software reports remain unchanged; the original instructions follow.

Restore **experiments/generated-drum-slice-copy-001/restore.wav** using the proven
stereo playback path and levels. Enter receive with **write + sound + record**, then
play the entire stereo PCM16/44100Hz transfer, approximately23.22seconds.

1. Confirm restore succeeds. Keep both knobs untouched.
2. **Before audition or pattern playback**, select **Sound8 / TONE**, with playback
   stopped and write off. Record a complete stereo backup at the same successful reduced
   levels as **experiments/edited-drum-slice-copy-001/capture.wav**. Let the dump finish
   and retain a second of silence before stopping the recording.
3. After saving, select **Sound10 / TONE**, write off, and tap **key1**. Confirm a clear
   short tone. Select **Sound9 / TONE** and tap **keys1 and2**; both previously accepted
   short tones should remain. Sound10/key1 now shares the same sample window as Sound9/key2;
   report any audible difference. Exact Tone/filter rendering is still unmeasured.
4. Return to **Sound8 / TONE**, playback stopped and write off. Report restore, tone
   checks and any deviations.

The candidate changes only packet415/selector24, copying Sound9/key2's entire reference
into Sound10/key1: `00000000d007000000` becomes **cd0f00009d17000000**. The destination
now stores start4045/end6045/owner0. Only payload offsets0/1/4/5 change. Both source
Sound9 references, all other Sound10 records, backing codes, melodic sounds, patterns
and every other plain packet must remain identical. No new packet or allocation is made.

- [Physical copy evidence](cross-drum-slice-copy-results.md)
- [Software validation](../experiments/generated-drum-slice-copy-001/software-validation.json)
- [Registered target](../experiments/edited-drum-slice-copy-001/restore-registration.json)
- [Hash-bound plan](../experiments/drum-slice-copy-plan-001/plan.json)
- Restore WAV SHA-256: `c48df513fb8565296957b620361f1c09ce48724911bdfb70d0d459bec2415d1f`
- Expected body SHA-256: `846092c09285da128689493f2a332fef8e0c22ac93fb710f9e0b994661fe971e`
- Exactly543 packets; frame end89844. Software phase/count/whole-body checks pass.
- Current genuine backup: `experiments/event-019-b-copy-drum9-key1-to-drum10-key1/capture.wav`.

The compiler/software reports remain `hardware_verified: false`. This generated
nonzero-start copy has not yet been restored. The physical zero-start copy's success
does not replace this device test. General drum mapping/allocation, destination endpoint
editing and exact endpoint inclusivity remain outside the supported scope.

Reproduce in a fresh folder:

```powershell
.\.venv\Scripts\python.exe -m scripts.make_cross_drum_slice_candidate --plan experiments/drum-slice-copy-plan-001/plan.json --out-dir experiments/generated-drum-slice-copy-002
```
