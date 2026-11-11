# Loop length test

FX 14 looped four steps from the pattern start and FX 11 and 12 repeated one step, while
FX 1, 2 and 15 changed nothing when held on steps 5 to 12
([FX pattern results](fx-pattern-results.md)). If those three are loops of 8, 12 and 16
steps, holding them over steps 2 to 16 must show replays for any loop shorter than the
pattern.

Patterns 1 to 5 play the sixteen-key run with FX 1, 2, 15, 14 and 11 held on steps 2 to
16. Pattern 6 is the control. Chain 1 to 6 at tempo 60, one cycle of 24 seconds. FX 14 and
11 are included as references that should read as loops of 4 and 1.

Registered before the session:

- **Reception.** The backup equals the target exactly.
- **Control run.** Key k on step k within 20 cents.
- **Loop lengths.** Each held effect is classified as the single loop length N in 1, 4, 8,
  12 or 16 whose prediction, key = ((step - 1) mod N) + 1, matches the key heard at
  100 ms on every held step, or unresolved.

The restore lasts about 75 seconds.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-loop-001
.\.venv\Scripts\python.exe -m scripts.check_fx_loop_test
```

- [Registration](../experiments/fx-loop-registration-001.json)
