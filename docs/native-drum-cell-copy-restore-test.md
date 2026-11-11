# Test copying the observed drum note into a layered step

Completed: the recapture matches the complete target with543 valid checksums, and the
user confirms restore, all requested grids and normal playback. See
[hardware results](native-drum-cell-copy-results.md) and the
[next physical key2 control](drum10-step9-key2-control.md). The original registration,
software reports and restore instructions are retained below.

Restore **experiments/generated-drum-cell-copy-001/restore.wav** through the proven
stereo playback path and levels. Enter receive with **write + sound + record**, then
play the entire stereo PCM16/44100Hz transfer, approximately23.22seconds.

1. Confirm restore succeeds. Keep both knobs untouched.
2. **Before inspecting step grids or playing the pattern**, select **Sound8 / TONE**,
   playback stopped and write off. Save a full stereo backup at the successful reduced
   recording levels as **experiments/edited-drum-cell-copy-001/capture.wav**. Let the dump
   finish and retain a second of silence before stopping the recording.
3. After saving, retain **Pattern1**. Select **Sound10** and enter write mode to inspect
   the grid: only **Steps1 and9** should be lit. Exit write without tapping any steps.
   Select **Sound2** and inspect only **Step9**; select **Sound3** and inspect
   **Steps1/5/9/13**. Exit write each time without toggling steps.
4. Play Pattern1 and confirm normal playback, then stop and return to Sound8/TONE,
   write off. Report restore, grid and playback outcomes and any deviations.

The candidate copies the observed Sound10 raw pair **0df883/10** from Step1 to empty
Sound10 Step9. Only Pattern1 bytes411/412/413/905 change from zero to13/248/131/16;
only native packets5/7 change. Source Step1, both existing melodic notes on Step9,
every other note/step, all samples/references, other15 patterns, footer and every other
plain packet remain identical. No key/parameter value is synthesized.

- [Physical note evidence](drum10-note-results.md)
- [Software validation](../experiments/generated-drum-cell-copy-001/software-validation.json)
- [Registered target](../experiments/edited-drum-cell-copy-001/restore-registration.json)
- [Hash-bound plan](../experiments/drum-cell-copy-plan-001/plan.json)
- Restore WAV SHA-256: `216b6e90d740e7b1a773e28af7e672fd8073b171b09f90047045fa051fd12001`
- Expected body SHA-256: `6f4e2cab0060a6ff1c63eaafe7b34ea7c4ee8e95fa5d2b88ee64d1c308e6c130`
- Exactly543 packets/end89844. Software phase/count/body checks pass.
- Genuine source backup: `experiments/event-020-b-drum10-key1-step1/capture.wav`.

This candidate's hardware acceptance is pending. Software/compiler reports remain
`hardware_verified: false`; its restoration and three-sound Step9 behavior need this
separate device test. The failed melodic F0 auxiliary prediction remains archived.
Scope stays Pattern1/Sound10/key1, its accepted copied sample context and calibrated
Sound2/Sound3 neighbors. Arbitrary keys, note parameters, sounds or polyphony are not
established by software copying alone.

Reproduce in a fresh folder:

```powershell
.\.venv\Scripts\python.exe -m scripts.make_drum_cell_candidate --plan experiments/drum-cell-copy-plan-001/plan.json --out-dir experiments/generated-drum-cell-copy-002
```
