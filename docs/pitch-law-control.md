# Per-step pitch-code law

A note's three primary bytes hold pitch (bits 0 to 4), an unknown bit 5, volume (6 to
11), filter (12 to 17) and resonance (18 to 23). Each field was located in its own
calibrated experiments, and the new codec in `formats/notes.py` matches all four
existing field modules on real captures. `set_step_parameters` is a public edit-plan
operation that writes one field per step and keeps every other bit.

Only pitch codes 13 and 14 have been measured, about one semitone apart. This test sets
all 16 Sound 3 notes to key 1 and gives each step its own pitch code across the observed
range 1 to 25: 13, 1, 25, 7, 19, 4, 22, 10, 16, 2, 24, 5, 21, 8, 18, 12. Both operations
run through the public plan path. The registered model is one semitone per code; the
alternative is that the codes are ignored. The frozen grid-only method measures every
step, and a model needs all 16 within 20 cents. See the
[plan](../experiments/pitch-law-plan-001/plan.json) and
[registration](../experiments/pitch-law-registration-001.json).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-pitch-law-001
.\.venv\Scripts\python.exe -m scripts.check_pitch_law_test
```

## First run and confirmation

The first run was received exactly, but its registered result was inconclusive. Each
note glides from the previous step's pitch for about 25 to 35 ms, and the 5 to 40 ms
window sat on that glide. Tracked over time, as an exploratory reading, every note then
held within about 2 cents of 100 cents per code, from -1198 at code 1 to +1201 at code
25. A key change does not glide, because it restarts the sample at a new rate.

The [confirmation](../experiments/pitch-law-confirm-registration-001.json) restores a
new code order (13, 25, 1, 19, 7, 22, 4, 16, 10, 24, 2, 21, 5, 18, 8, 14) and measures 50
to 90 ms after each note, with the frozen grid method otherwise unchanged.

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-pitch-law-002
.\.venv\Scripts\python.exe -m scripts.check_pitch_law_confirm
```
