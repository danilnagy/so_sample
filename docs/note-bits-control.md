# Note bits test: pitch code 0 and bit 5

Two bits of a note's primary bytes are still unexplained. Pitch code 0 has never been
played, and bit 5 has never been seen set. Pattern 2 plays Sound 1 at key 1 on every
step, with the chain set to Pattern 2 alone:

| Step | Pitch code | Bit 5 |
| --- | --- | --- |
| 1 | 13 | |
| 2 | 19 | |
| 3 | 0 | |
| 4 | 7 | |
| 5 | 0 | |
| 6 | 25 | |
| 7 | 25 | set |
| 8 | 13 | |
| 9 | 13 | set |
| 10 | 1 | |
| 11 | 0 | |
| 12 | 25 | |
| 13 | 25 | set |
| 14 | 13 | |
| 15 | 0 | |
| 16 | 13 | |

Registered before the session:

- **Pitch code 0.** `zero_holds_last_pitch` predicts each code-0 step repeats the pitch
  before it, as the other parameters do. `zero_is_pitch_13` and `zero_is_below_code_1` are
  the alternatives.
- **Bit 5.** `bit5_inert` holds when each flagged note matches the note before it within
  20 cents, 1.5 dB and, on the pitch-25 pairs, 5 ms of duration. If the device clears the
  bit, the backup differs from the target only in those bits; that is recorded as
  `bit5_cleared_by_device`.

The restore lasts about a minute.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-note-bits-001
.\.venv\Scripts\python.exe -m scripts.check_note_bits_test
```

- [Registration](../experiments/note-bits-registration-001.json)
