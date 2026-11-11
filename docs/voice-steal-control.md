# Voice stealing test

With [four voices](polyphony-results.md), a long note may still be sounding when later
steps start new notes. Does a fifth note cut the old one, or does it get dropped?

Melodic key 13 plays an octave below key 1, so a 0.5 s melodic tone lasts 1.0 s, four
steps. Pattern 2 plays each voice alone. Pattern 3 holds four scenarios:

| Scenario | Long note | Then | Then |
| --- | --- | --- | --- |
| A | step 1: Sound 1 key 13 | step 2: Sounds 2 3 4 | step 3: Sound 5 |
| B (control) | step 5: Sound 1 key 13 | step 6: Sounds 2 3 | step 7: Sound 5 |
| C | step 9: Sound 8 key 13 | step 10: Sounds 11 12 14 | step 11: Sound 1 |
| D | step 13: Sound 8 key 13 | | step 15: Sounds 1 2 3 4 |

Registered before the session, as the presence of the long note and the new note after
each overflow:

- **drop_new.** The fifth note does not play and the long note continues.
- **steal_oldest.** The fifth note plays and the long note is cut.
- **lowest_sound_wins.** The lowest sound numbers keep playing. In scenario C, Sound 1
  plays and Sound 8 continues; in D, Sound 8 is cut.

Scenario B should keep every note. You should hear whether the long low notes get cut
short. The restore lasts about 3.4 minutes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-voice-steal-001
.\.venv\Scripts\python.exe -m scripts.check_voice_steal_test
```

- [Registration](../experiments/voice-steal-registration-001.json)
