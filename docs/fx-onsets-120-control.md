# FX onsets observation at 120 BPM

At 60 BPM, FX 9 cut notes short, FX 10 gated the third and fourth of every four steps,
FX 12 retriggered every 250 ms and FX 13 echoed the note from two steps earlier. This
observation measures their onset timing at 120 BPM, where a step lasts 125 ms, to see
which follow the tempo.

Patterns 1 to 4 play the sixteen-key run with FX 9, 10, 12 and 13 held on steps 5 to 12.
Pattern 5 is the control. Chain 1 to 5; two cycles of 10 seconds are recorded. Each step
is read for its onsets and the key heard 50 ms in.

Registered before the session:

- **Reception.** The backup equals the target exactly.
- **Control run.** Key k on step k within 20 cents, one onset per step.

Everything else is description. The restore lasts about 75 seconds.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-onsets-120-001
.\.venv\Scripts\python.exe -m scripts.check_fx_onsets_120_observation
```

- [Registration](../experiments/fx-onsets-120-registration-001.json)
