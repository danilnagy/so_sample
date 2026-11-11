# Parameter-only lock test

The device stores a lock on a step without a note as a parameter-only cell: primary bytes
with a zero auxiliary byte. A note with code 0 keeps the last locked value. This test asks
whether locks on empty steps count.

From the no-lock state, the chain becomes 1, 2, with Sound 16's sawtooth on odd steps:

- **Pattern 1.** Notes on steps 1, 7, 11 and 15 lock filter 63, 63, 56 and 63. Notes on
  steps 3, 5, 9 and 13 are unlocked (code 0). Steps 2, 4, 8 and 12 hold no note but
  parameter-only filter locks of 24, 50, 20 and 24, written by the new
  `set_parameter_locks` operation.
- **Pattern 2.** Notes locked to 63, 24, 50, 63, 20, 56, 24 and 63 as references.

Models, registered before the session:

- **param_only_sets_value.** The unlocked notes play at 24, 50, 20 and 24.
- **param_only_ignored.** They play at the last note lock: 63, 63, 63 and 56.

A model holds when every unlocked note matches its reference within 1.5 dB over five
chain cycles. The backup must equal the compiled target exactly.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-param-only-001
.\.venv\Scripts\python.exe -m scripts.check_param_only_test
```

- [Registration](../experiments/param-only-registration-001.json)
