# Hardware test of the melodic notes writer

`set_melodic_notes` is a public edit-plan operation. For one pattern and one melodic
sound (1 to 8) it takes 16 entries, step 1 first, each `null` or a key 1 to 16. Notes
copy the parameter bytes of that sound's existing notes in the pattern, which must be
identical; the key goes in the auxiliary byte's low nibble with F above it, and `null`
clears the cell.

This test compiles a hash-bound plan through `apply-edits` from the verified keyboard
scale state and writes the melody 16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8
on Sound 3, using every key once. The confirmed row layout predicts each step's interval
from step 1; keeping the previous key order is registered as the alternative. The frozen
grid-only method measures every step on fresh recordings, and a model needs all 16 steps
within 20 cents. See the [plan](../experiments/melodic-notes-plan-001/plan.json) and
[registration](../experiments/melodic-notes-writer-registration-001.json).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-melodic-notes-writer-001
.\.venv\Scripts\python.exe -m scripts.check_melodic_notes_writer_test
```
