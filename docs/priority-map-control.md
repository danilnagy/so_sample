# Priority map test

On a shared step the four lowest-numbered sounds play, except that Sound 11 beat Sound 4
while Sound 16 lost to it ([voice priority results](voice-priority-results.md)). This test
pits each drum 11 to 16 against Sounds 1 to 4, and Sound 11 against Sound 5. Swing returns
to 0 and the chain to 2, 3. Pattern 2 plays each of the eleven voices alone.

| Step | Sounds |
| --- | --- |
| 1 | 1 2 3 4 11 |
| 3 | 1 2 3 4 12 |
| 5 | 1 2 3 4 13 |
| 7 | 1 2 3 4 14 |
| 9 | 1 2 3 4 15 |
| 11 | 1 2 3 4 16 |
| 13 | 1 2 3 5 11 |
| 15 | 2 3 4 5 11 |

Registered before the session:

- **four_voices.** Every stack sounds exactly four.
- **lowest_sounds_win.** The four lowest numbers play in every stack.
- **sound11_outranks_4_and_5.** Sound 11 ranks right after Sound 3; everything else by
  number.

The measured set per stack is reported whatever happens. The restore lasts about 70
seconds.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-priority-map-001
.\.venv\Scripts\python.exe -m scripts.check_priority_map_test
```

- [Registration](../experiments/priority-map-registration-001.json)
