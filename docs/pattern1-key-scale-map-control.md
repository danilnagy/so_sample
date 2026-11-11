# Melodic keyboard scale map

Only keys 1, 2, 7 and 16 of a melodic sound have been written, and their pitches were
never measured. This control measures all sixteen. From the verified writer-test state
(16 Sound 3 notes, 60 BPM, swing 0), Pattern 1's effects are cleared and step s plays
key s, auxiliary byte `F0 | (s - 1)`. Every note keeps the same primary bytes.

Each note's pitch is the median over windows 5 to 40 ms after its onset, since higher
keys play the sample faster and shorter. Intervals are in cents relative to step 1. The
registered models are chromatic (key k is k - 1 semitones up), major and natural minor;
a model needs every step within 20 cents in its five-loop median and in four of five
loops. The measured table is reported either way. On the writer-test playback, the
method resolves an exact octave to within about 2 cents. See the
[registration](../experiments/pattern1-key-scale-map-registration-001.json) and
[method](../scripts/pattern1_key_scale_method.py).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-key-scale-map-001
.\.venv\Scripts\python.exe -m scripts.check_pattern1_key_scale_map
```

## First run and rerun

The first run was received exactly, but the playback ran at 80 BPM after an accidental
tempo change, so the registered decision was inconclusive. Read on the actual 80 BPM
grid, as an exploratory check, the keys formed whole-semitone rows on the 4x4 key grid,
in cents from key 1:

| Keys | Cents |
| --- | --- |
| 1 to 4 | 0, 100, 300, 400 |
| 5 to 8 | -700, -500, -400, -200 |
| 9 to 12 | -1200, -1100, -900, -800 |
| 13 to 16 | -1900, -1700, -1600, -1400 |

Low keys play longer than a step and each new note cuts the previous one, so the
[rerun registration](../experiments/pattern1-key-scale-map-rerun-registration-001.json)
measures on the step grid alone, searches down to 300 Hz, and adds this row layout as a
fourth model. Keep the BPM untouched during the session.

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-key-scale-map-002
.\.venv\Scripts\python.exe -m scripts.check_pattern1_key_scale_map_rerun
```
