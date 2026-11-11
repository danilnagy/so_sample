# Integer tempo edit plans

`set_tempo` changes the verified integer BPM field within 60 to 240:

```json
{"operation": "set_tempo", "bpm": 137}
```

Use the existing source-hash-bound plan schema and a fresh output directory:

```powershell
.\.venv\Scripts\python.exe -m po33_re apply-edits experiments/event-036-a-return-fine-tempo-100/derived/analysis-001/capture.symbols.npz --plan experiments/replay-fine-tempo137-plan-001/plan.json --out-dir experiments/example-fine137-001
```

Source BPM must also be within 60 to 240. The two 255-byte global records must be at
packet indices 1/2 and match the recognized opaque-record hashes, masking only second
record bytes 129 (tempo) and 130 (swing). Source swing must remain within the supported
0 to 18 numeric range and is preserved during tempo editing. Unknown global settings
are rejected, never reset to a template. Every
unrelated packet remains literal, including samples, patterns and sound parameters.
Equal source/target BPM is a no-op. Bool, float, string and out-of-range arguments fail.

Physical 60/80/100/120/140/240 controls, exact returns and generated 80/137 restores
support the mapping and range policy. The guide documents 60 to 240. The 137 restore
tests an unobserved intermediate value; every integer is not individually hardware
tested. See [hardware results](generated-fine-tempo137-results.md).

The API functions are `calibrated_tempo(frame)` and `set_calibrated_tempo(frame, bpm)`.
The original `set_tempo_preset` operation and preset APIs retain their strict three-preset
source/target contract for compatibility. Use `set_tempo` for fine sources, including
a preset destination. The public 137 plan replays the accepted WAV byte-for-byte; general
editing also reproduces every independently genuine observed tempo body.

Compiler reports remain software-only. Project JSON remains read-only. The expanded
global guard is grounded in [verified swing controls and restore](generated-swing6-results.md).
The next [joint tempo/swing test](joint-tempo-swing-control.md) checks the new combination
on hardware; the preset-only source/target BPM contract remains unchanged.
