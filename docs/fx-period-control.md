# FX period test

The [direction test](fx-direction-results.md) read FX 1 and 2 as loops of about 250 and
333 ms of the sample's start, and FX 3, 4 and 12 as shorter loops or retriggers. This test
measures each repetition period directly.

Patterns 1 to 5 play Sound 6's four-segment sample on steps 1 and 5 with FX 1, 2, 3, 4 and
12 held on steps 5 to 16, so the second note sits under the effect for three seconds.
Pattern 6 is the control. Chain 1 to 6 at tempo 60.

A new frozen method, `scripts/fx_period_method.py`, tracks the dominant pitch every
10 ms over 1.2 s of the held note and finds the lag at which the track best repeats.

Registered before the session:

- **Reception.** The backup equals the target exactly.
- **Control.** The control's note has no repetition period.
- **Per effect.** Classified as the single candidate within 8% of the measured period,
  from 1/8, 1/12, 1/16, 1/24, 1/32, 1/48 and 1/64 of the 4 s bar, otherwise unresolved.

The restore lasts about 75 seconds.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-period-001
.\.venv\Scripts\python.exe -m scripts.check_fx_period_test
```

- [Registration](../experiments/fx-period-registration-001.json)
