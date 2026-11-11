# Hardware test of the per-step effect writer

`set_step_effects` is a public edit-plan operation. It takes a pattern and 16 entries,
step 1 first, each `null` or an FX key 1 to 15, and changes only that pattern's eight
footer bytes using the confirmed layout and code map.

This test compiles a hash-bound plan through the public `apply-edits` path from the
verified 16-note, 60 BPM state. It puts FX key 7 (octave up) on steps 1, 4, 7, 8, 9, 12,
15 and 16, the complement of the earlier layout, giving footer `6F F6 FF 66 6F F6 FF 66`.
The restore replaces the device state, so the backup must match the compiled target
exactly. The frozen per-note-gate method then classifies all 16 notes on the fresh
playback. The sequential layout predicts exactly the planned steps; a model needs every
step to match in its five-loop median and at least four of five loops.

See the [plan](../experiments/step-effects-plan-001/plan.json),
[registration](../experiments/step-effects-writer-registration-001.json) and
[compile report](../experiments/compiled-step-effects-writer-001/compile-report.json).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-step-effects-writer-001
.\.venv\Scripts\python.exe -m scripts.check_step_effects_writer_test
```
