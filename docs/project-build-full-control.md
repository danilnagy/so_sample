# Full project build

The first [project build](project-build-results.md) used two imports and two patterns.
This one fills the device from a single spec through `po33_re.project_build`:

- eight melodic imports, 0.3 s tones a semitone apart from 220 Hz;
- eight drum kits of sixteen 43 ms tones each;
- sixteen patterns, each with a kick on Sound 13, hats on Sound 11 with a volume lock on
  step 16, a melody on a different melodic sound per pattern with alternating filter
  settings, and an effect on step 16; pattern 1 alone carries a snare on Sound 14;
- a chain of eight patterns, tempo 128, swing 6.

Registered before the session:

- **Reception.** The backup equals the built target exactly.
- **tempo_128.** Sound 13 onsets are 0.469 s apart within 5 ms.
- **chain_8.** Sound 14 bursts recur every chain cycle, 15.0 s, within 20 ms.
- **melody_first_note.** Pattern 1's melody sound at key 1 sounds in step 1 and not in
  step 2 by at least 20 dB.

The restore is longer than recent ones because every slot carries new audio.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/project-build-full-001/compiled
.\.venv\Scripts\python.exe -m scripts.check_project_build_full_test
```

- [Registration](../experiments/project-build-full-registration-001.json)
- [Build report](../experiments/project-build-full-001/build-report.json)
