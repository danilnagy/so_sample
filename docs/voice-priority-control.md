# Voice priority test

The PO-33 plays [four voices](polyphony-results.md). This test maps which four survive
when more sounds share a step. Pattern 2 still plays the fourteen tones one at a time.
Pattern 3's stacks become eight sets chosen so that candidate rules disagree:

| Step | Sounds |
| --- | --- |
| 1 | 1 2 3 4 11 |
| 3 | 1 2 3 4 16 |
| 5 | 1 2 3 4 5 |
| 7 | 4 5 6 7 8 |
| 9 | 1 11 12 13 14 |
| 11 | 1 2 11 12 13 |
| 13 | 11 12 13 14 15 |
| 15 | 1 2 3 11 12 13 14 15 16 |

The frozen method is the corrected onset variant, `scripts/polyphony_method_exploratory.py`,
now registered by hash.

Registered before the session:

- **four_voices.** Every stack sounds exactly four.
- **lowest_sounds_win**, **highest_sounds_win**, **drums_win.** Each predicts the four
  that play; a rule holds when it matches every stack. Melodic sounds always have the
  lower numbers, so "melodic first" is the same as lowest_sounds_win.

The measured set per stack is reported whatever happens. You should hear eight chords of
four notes. The restore lasts about 3.4 minutes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-voice-priority-001
.\.venv\Scripts\python.exe -m scripts.check_voice_priority_test
```

- [Registration](../experiments/voice-priority-registration-001.json)
