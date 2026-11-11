# Melodic keyboard scale map: a row layout on the 4x4 key grid

The [registered rerun](pattern1-key-scale-map-control.md) supports the row layout. The
restore was received exactly, and every key's pitch fell within half a cent of the
prediction, in its five-loop median and in at least four of five loops. Chromatic, major
and natural minor are all rejected. Key 1 measured 1190.57 Hz.

| Keys (row) | Semitones from key 1 |
| --- | --- |
| 1, 2, 3, 4 (top) | 0, +1, +3, +4 |
| 5, 6, 7, 8 | -7, -5, -4, -2 |
| 9, 10, 11, 12 | -12, -11, -9, -8 |
| 13, 14, 15, 16 (bottom) | -19, -17, -16, -14 |

Each row of the 4x4 button grid covers its own register: lower rows are lower, and pitch
rises left to right within a row. Sorted, the sixteen keys form one continuous run from
-19 to +4 semitones. The key is stored in the auxiliary byte's low nibble, key - 1, with
F in the high nibble for this melodic sound. Lower keys play the sample slower and so
last longer, and a new note on the same sound cuts the previous one.

The row layout came from an exploratory reading of the first run, which played back at
80 BPM after an accidental tempo change; this rerun is its registered confirmation on
fresh recordings. See the [decision](../experiments/pattern1-key-scale-map-rerun-decision-001.json)
and [observation](../experiments/edited-pattern1-key-scale-map-002/hardware-observation-001.json).
Current genuine export: `experiments/exported-pattern1-key-scale-map-002/project.json`.

Scope: Sound 3 with its recorded parameters. Other melodic sounds are expected to share
the layout but were not measured.
