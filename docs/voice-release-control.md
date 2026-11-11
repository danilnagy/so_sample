# Voice release test

A fifth note took a voice that had 84 ms left and was dropped when the only busy voice had
500 ms left ([voice stealing results](voice-steal-results.md)). This test varies the time
left using pitch codes, which scale a note's length by 2^((13 - code) / 12).

Each scenario is four steps. Sound 1 at key 13 plays a 1.0 s note at 200 Hz. One step
later Sounds 2, 3 and 4 play at the scenario's pitch code. One step after that Sound 5
arrives as the fifth note, while the three short notes have:

| Scenario | Pitch code | Time left on the short notes |
| --- | --- | --- |
| 1 | 1 | 417 ms |
| 2 | 7 | 222 ms |
| 3 | 13 | 84 ms |
| 4 | 19 | ended 14 ms earlier |

Pattern 2 plays each of the fourteen voices alone. Registered before the session, as the
presence of each voice when Sound 5 arrives:

- **never_steal.** Sound 5 plays only in scenario 4.
- **steal_nearest_end.** Sound 5 always plays and takes Sound 4's voice.
- **release_under_100ms.** Sound 5 plays in scenarios 3 and 4 only; nothing is cut.
- **steal_oldest.** Sound 5 always plays and the long note is cut.

**Smaller package.** Transfer time is almost all sample data, and the tests since the
filter law only play key 1 of each drum kit. This restore first re-imports every drum kit
slim: the key-1 tone byte-identical, keys 2 to 16 as 20 ms of silence, 4 pages per kit
instead of 25 (`scripts/slim_drum_kits.py`). The package falls from 745472 to 212992
sample codes, and the restore from about 3.4 minutes to about 1 minute. The backup
shrinks by the same amount.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-voice-release-001
.\.venv\Scripts\python.exe -m scripts.check_voice_release_test
```

- [Registration](../experiments/voice-release-registration-001.json)
