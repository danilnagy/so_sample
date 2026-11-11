# Full 16-step effect map at 60 BPM

The position map confirmed the high nibbles of footer bytes 0, 2, 4 and 6. This control
observes all 16 step positions at once. Pattern 1 gets the same Sound 3 note on every
step, at 60 BPM (250 ms steps, so the 210 ms notes do not overlap) and swing 0. Both are
inside the hardware-verified tempo and swing ranges.

The footer `F6 6F 66 FF F6 6F 66 FF` puts the rising effect code 6 on steps 2, 3, 5, 6,
10, 11, 13 and 14. Every byte gets a different high/low combination, so a swapped,
shifted or reversed layout gives a different set of rising notes.

| Model | Rising steps |
| --- | --- |
| Sequential, high nibble first | 2, 3, 5, 6, 10, 11, 13, 14 |
| Sequential, low nibble first | 1, 4, 5, 6, 9, 12, 13, 14 |

Each note is found on the 250 ms step grid, refined to its rising edge within 30 ms, and
classified 20 to 130 ms after onset with the frozen thresholds. A model needs all 16
steps, each matching in its five-loop median and at least four of five loops. The
observed per-step map is reported either way. The grid method replaced a minimum-gap
onset rule that fails when notes are this close; on the earlier position-map playback
it reproduces that registered result, with every note within 1.7 ms of the grid. See
the [registration](../experiments/pattern1-FX-full-step-map-registration-001.json) and
[method](../scripts/pattern1_fx_grid_pitch_method.py).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-FX-full-step-map-001
.\.venv\Scripts\python.exe -m scripts.check_pattern1_fx_full_step_map
```
