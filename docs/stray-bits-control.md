# Stray bits observation

Two fields in a backup still have no measured meaning:

- the **auxiliary byte's high nibble**, only ever seen as F (melodic note) or 1 (drum
  note);
- **global bytes 131 to 146** of the second global record, one per pattern, which changed
  after playback stops and were read as a per-pattern stop step.

Pattern 2 plays Sound 8's C5 tone on every odd step. The even steps hold raw cells written
by research-only operations:

| Step | Sound | Cell |
| --- | --- | --- |
| 2 | 8 | normal parameters, auxiliary 20 hex |
| 4 | 8 | normal parameters, auxiliary 10 hex: the drum nibble on a melodic sound |
| 6 | 13 | normal parameters, auxiliary F0 hex: the melodic nibble on a drum sound |
| 8 | 8 | normal parameters, auxiliary E0 hex |
| 10 | 8 | normal parameters, auxiliary 00: a parameter-only cell, as a control |
| 12 | 8 | pitch field 0, auxiliary F5 hex: melodic key 6 with the pitch unlocked |

Global bytes 131 to 146 are set to 1 to 16. The chain is Pattern 2 alone, swing 0, tempo
100.

Registered before the session:

- **raw_values_kept.** The backup equals the target exactly.
- **odd_steps_normal.** Every odd step sounds Sound 8 within 10 dB of step 1.

Reception is classified per raw cell and per global byte as kept, rewritten or cleared.
What each even step plays, and at which frequency, is read exploratively with no
prediction. The restore lasts about 75 seconds.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-stray-bits-001
.\.venv\Scripts\python.exe -m scripts.check_stray_bits_test
```

- [Registration](../experiments/stray-bits-registration-001.json)
