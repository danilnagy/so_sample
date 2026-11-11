# Write Pattern 5 and select it

Every pattern writer so far has been verified on Pattern 1 only. Byte 0 of the second
global record read 15 in the one backup taken after Pattern 16 was selected, and 0 in
every other backup, so it may hold the selected pattern counted from zero.

Through the public plan path, with two new operations:

1. `copy_pattern` copies Pattern 1 to Pattern 5.
2. `set_melodic_notes` reverses Pattern 5, so its eight tones fall instead of rise.
3. `set_selected_pattern` sets byte 0 to 4, selecting Pattern 5.

**Press only play.** Don't touch any pattern button, so the device plays whatever it
treats as selected.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly.
- **pattern5_selected.** Eight falling tones: -150 cents per pair of steps, and step 1
  at 1099.1 Hz.
- **pattern1_plays.** Eight rising tones: +150 cents per pair of steps, and step 1 at
  599.3 Hz.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-selected-pattern-001
.\.venv\Scripts\python.exe -m scripts.check_selected_pattern_test
```

- [Registration](../experiments/selected-pattern-registration-001.json)
- [Plan](../experiments/selected-pattern-plan-001/plan.json)
