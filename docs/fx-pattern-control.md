# FX pattern observation

Six effects left a single note untouched in the [FX catalogue](fx-catalog-results.md), so
they must act on the pattern as a whole. This observation gives every effect a run of
different notes to work on.

Patterns 1 to 15 each play Sound 8's C5 tone on every step with keys 1 to 16 in order,
sixteen distinct pitches, and effect k on steps 5 to 12 of pattern k. Pattern 16 is the
same run with no effect, the control. The chain is 1 to 16 at tempo 60, so one cycle lasts
64 seconds and the playback records one cycle.

A new frozen method, `scripts/fx_pattern_method.py`, reads each step's dominant pitch at
100 and 180 ms, maps it to the nearest key, and counts onsets within the step.

Registered before the session:

- **exact_reception.** The backup equals the target exactly.
- **control_run.** The control pattern plays key k on step k within 20 cents, one onset
  per step.

Every other pattern is described, not predicted. The restore lasts about 75 seconds and
the playback recording a little over a minute.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-pattern-001
.\.venv\Scripts\python.exe -m scripts.check_fx_pattern_observation
```

- [Registration](../experiments/fx-pattern-registration-001.json)
