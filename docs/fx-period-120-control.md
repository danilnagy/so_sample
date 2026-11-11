# Tempo-sync test for the loop effects

At 60 BPM the loop effects divide the bar: FX 1 loops 1/16, 2 1/12, 3 1/32, 4 1/48, and
FX 12 retriggers every 1/16 ([period results](fx-period-results.md)). Do they follow the
tempo? The same five effects are measured at 120 BPM, with the four-segment sample on
steps 1 and 5 and the effect held on steps 5 to 16 of patterns 1 to 5; pattern 6 is the
control.

The period method scores each lag by the fraction of track pairs that differ by more than
50 cents (`scripts/fx_period_median_method.py`), which ignores the single-window glitches
at loop boundaries that left FX 1, 2 and 3 unresolved before.

Registered before the session:

- **Reception.** The backup equals the target exactly.
- **Control.** The control's note has no repetition period.
- **tempo_synced.** Periods halve: 125, 167, 62.5, 41.7 and 125 ms for FX 1, 2, 3, 4, 12.
- **fixed_ms.** Periods stay at 250, 333, 125, 83 and 250 ms.

A model holds when every effect's measured period is within 8 percent of its prediction.
The restore lasts about 75 seconds.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-period-120-001
.\.venv\Scripts\python.exe -m scripts.check_fx_period_120_test
```

- [Registration](../experiments/fx-period-120-registration-001.json)
