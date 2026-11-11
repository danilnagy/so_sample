# FX direction test

FX 1, 2 and 15 change nothing on a pure tone, and FX 3, 4 and 12 extend a note without
showing how ([loop results](fx-loop-results.md)). A pure tone cannot reveal reversed
playback or a loop of part of a sample. Sound 6 holds a 1.0 s sample of four segments at
400, 500, 600 and 700 Hz; its window returns to the whole sample, so a key-1 note plays
the four segments in 667 ms.

Patterns 1 to 8 play Sound 6 on steps 1, 5, 9 and 13 with FX 1, 2, 15, 3, 4, 12, 11 and
13 held on steps 5 to 16, so each pattern's first note is plain and the next three are
under the effect. Pattern 9 is the control. Chain 1 to 9 at tempo 60, one cycle of 36 s.

A new frozen method, `scripts/fx_direction_method.py`, reads which segment sounds in five
windows across each note and counts onsets.

Registered before the session:

- **Reception.** The backup equals the target exactly.
- **Plain notes forward.** The control's notes and every pattern's first note play
  segments 1, 2, 3, 4 then silence.
- **Per effect.** Classified as forward, reverse (4, 3, 2, 1) or hold_first (segment 1
  throughout) when all three held notes agree, otherwise described.

The restore lasts about 75 seconds and the playback about 40.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-direction-001
.\.venv\Scripts\python.exe -m scripts.check_fx_direction_test
```

- [Registration](../experiments/fx-direction-registration-001.json)
