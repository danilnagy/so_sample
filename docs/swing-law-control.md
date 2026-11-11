# Swing law test at swing 18

The swing byte, byte 130 of the second global record, shows 0 to 18 on the device. The
one timing measurement so far, a generated swing 6 at 137 BPM, delayed each even step by
27.2 ms, putting it at position 0.624 of the two-step interval instead of 0.5. The scale
is unknown.

This test sets swing to its maximum, 18, at 60 BPM. Sound 6's window becomes a 2000-code
click of 57 ms, played on every step of Pattern 2, so onsets are sharp. A new frozen
method, `scripts/swing_onset_method.py`, finds each click and measures where every even
step falls between its odd neighbours.

Registered before the session:

- **linear_in_code.** Position 0.872: three times the swing-6 delay.
- **triplet_at_max.** Position 0.667, the classic maximum swing.
- **three_quarters_at_max.** Position 0.75.

A model holds when the five-loop median is within 0.02 of it and the spread across all
even steps and loops is below 0.04. The backup must equal the compiled target exactly.
The swing writer used here, `set_swing_byte`, works in any global layout.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-swing-law-001
.\.venv\Scripts\python.exe -m scripts.check_swing_law_test
```

- [Registration](../experiments/swing-law-registration-001.json)
