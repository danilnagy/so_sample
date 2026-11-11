# Aux-nibble test 3: retrigger spacing and note length against tempo and swing

Registered 2026-11-11. [aux-nibble-001](aux-nibble-results.md) measured, at 60 BPM with no
swing, that a drum's retrigger of n plays n hits a step apart divided by n, and a melodic
length of n lasts n steps. This session asks whether both follow the tempo and what swing
does to them, at 120 BPM (a 125 ms step) with swing 12, which delays even steps by half a
step, 62.5 ms ([swing law](swing-law-results.md)).

## Build

`web/scripts/build-aux-nibble-3-test.ts` writes raw auxiliary bytes after each cell and
asserts the layout before writing. 25 pages, a 33 s restore.
`scripts/prepare_aux_nibble_3_test.py` decodes the restore with the Python decoder, requires
it to carry the compiler's packets, pins the frozen method (`scripts/aux_nibble3_method.py`)
by hash and registers the predictions below.

| Patterns | Content |
| --- | --- |
| 1 to 3 | a 6 ms 5 kHz click on Sound 9, retriggered 2, 3, 4, 6 and 8 times, each on an odd step (1 or 9) and an even, swung step (6 or 14) |
| 4 to 7 | lengths 1, 2, 3 and 4: on step 1 (odd) a 700 Hz tone on Sound 1, on step 2 (even) a 1000 Hz tone on Sound 2 |

Chain 1 to 7, 14 s a pass; the playback recording holds four passes (60 s).

## Predictions

Registered before the session. Spacing: the median gap between a retrigger's first n
onsets, for n = 2, 3, 4, 6 on each parity, within 3 ms. Length: how long each note sounds,
within 25 ms.

| | Prediction | Odd step | Even (swung) step |
| --- | --- | --- | --- |
| Reception | the backup equals the target exactly, auxiliary bytes, tempo and swing included | | |
| Spacing | **H_spacing_scales_with_step**: repeats divide the tempo's step | 125/n ms | 125/n ms |
| | **H_spacing_spans_swung_step**: repeats divide the time to the next step as swing places it | 187.5/n ms | 62.5/n ms |
| | **H_spacing_fixed_time**: spacing does not follow tempo | 250/n ms | 250/n ms |
| Length | **H_length_scales_with_step**: n of the tempo's steps from the note's own start | n x 125 ms | n x 125 ms |
| | **H_length_ends_on_swung_grid**: the note ends where step start + n begins, as swing places it | n x 125 + 62.5 ms for odd n | n x 125 - 62.5 ms for odd n |
| | **H_length_fixed_time**: length does not follow tempo | n x 250 ms | n x 250 ms |

The spacing hypotheses exclude each other; the length hypotheses exclude each other on odd
lengths (on even lengths the first two agree). If none holds, the result is recorded as
neither and no rule is adopted. Exploratory: retrigger 8 (7.8 to 31.3 ms gaps, near the
method's 6 ms resolution), the onset counts, each probe's start offset from the grid (which
should show the 62.5 ms swing on even steps) and the session answers.

## Running it

From the repository root, on macOS (on Windows use `.\.venv\Scripts\python.exe`). The build
and the registration are done:

```
cd web && npx tsx scripts/build-aux-nibble-3-test.ts && cd ..
.venv/bin/python -m scripts.prepare_aux_nibble_3_test
```

The session:

```
.venv/bin/python -m po33_re hw run experiments/aux-nibble-003
.venv/bin/python -m scripts.check_aux_nibble_3_test
.venv/bin/python -m scripts.finalize_aux_nibble_3_test
```

1. Cables: the computer's headphone output to the PO-33's input; the PO-33's output
   unplugged. On the PO-33, hold write and press sound + record. `hw run` plays the restore
   (about 33 s).
2. When prompted, swap: unplug the computer's output from the PO-33, connect the PO-33's
   output to the computer's stereo line input. Press write + sound + play when asked; the
   harness records the backup and checks it against the target.
3. When asked, press PLAY on the PO-33 and let four passes play (60 s) without touching
   anything, then answer the questions.

- [Registration](../experiments/aux-nibble-registration-003.json)
- [Experiment](../experiments/aux-nibble-003/experiment.json)
