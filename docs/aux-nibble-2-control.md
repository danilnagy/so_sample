# Aux-nibble test 2: retrigger voices and choke, and the remaining note lengths

Registered 2026-11-11. [aux-nibble-001](aux-nibble-results.md) found that a note's auxiliary
high nibble is a drum's retrigger count and a melodic note's length in steps, measured for
retriggers 1, 2, 3, 4, 6, 8 and lengths 1, 2, 4, 8. Before the app writes and previews them,
this session asks what a preview has to model: how a drum's repeats use the four voices,
whether a repeat cuts the one before it, and how long the lengths not yet measured last. It
runs at 60 BPM with no swing; [aux-nibble-003](aux-nibble-3-control.md) covers tempo and
swing.

## Build

`web/scripts/build-aux-nibble-2-test.ts` writes raw auxiliary bytes after each cell (as
aux-nibble-001 did) and asserts, before writing anything, that every byte and effect reaches
the compiled patterns and that the notes are exactly the probes. 109 pages, a 123 s
restore. `scripts/prepare_aux_nibble_2_test.py` decodes the restore with the Python decoder,
requires it to carry the compiler's packets, pins the frozen method
(`scripts/aux_nibble2_method.py`) by hash and registers the predictions below.

| Sound | Sample | Used for |
| --- | --- | --- |
| 9, key 1 | the drum: a 7 kHz click (its onset) and a 1 s noise body around 3 kHz, decaying | retriggers, voices, choke |
| 1, 2, 3 | 2.5 s tones at 250, 350, 500 Hz, played for 8 steps (nibble 8, 2 s) | holders: busy voices |
| 5, 6 | 5 s tones at 700 and 1000 Hz | length probes |

| Patterns | Content |
| --- | --- |
| 1 | the drum once (step 1, the reference) and retriggered 4 times alone (step 9) |
| 2, 3, 4 | 1, 2, 3 holders from step 1, and the drum retriggered 4 times on step 5, a second in |
| 5 to 8 | exploratory: FX 13 (steps 1 to 8) and FX 14 (steps 5 to 12) over the retrigger of 4 and over a two-step 700 Hz note |
| 9 to 13 | two length probes a bar: 3 and 5, 6 and 7, 9 and A, B and C, D and E |
| 14 | the length probe F alone |

Chain 1 to 14, 56 s a pass; the playback recording holds two passes (118 s).

## Predictions

Registered before the session, in pairs that exclude each other; if neither of a pair holds,
the result is recorded as neither and no rule is adopted.

| Question | Prediction | Measured as |
| --- | --- | --- |
| Reception | the backup equals the target exactly, every auxiliary byte and effect included | native check |
| Voices | **H1_one_voice**: repeats re-strike one voice, so all 4 sound with 0, 1, 2 or 3 voices held | click onsets in the drum's step: 4, 4, 4, 4 |
| | **H2_voice_per_repeat**: each repeat needs a free voice and is dropped without one (a sounding note is never cut) | 4, 3, 2, 1 |
| Choke | **H1_restart**: a repeat cuts the one before and restarts the sample | body power 12 to 52 ms after the 4th onset of the lone retrigger, against the single hit's after its onset: 0 dB within 1.5 dB |
| | **H2_overlap**: repeats keep sounding and add up | the single hit's body summed at 0, 62.5, 125 and 187.5 ms (predicted from the reference, about +4 dB) within 1.5 dB |
| Holders | **H_holders_continue**: no holder is cut by the drum | every holder sounds 2.0 s within 60 ms |
| Lengths | **H_length_steps**: nibble n in 3, 5, 6, 7, 9, A, B, C, D, E sounds n steps | n x 250 ms within 60 ms |
| F | **H_F_15_steps**: F is fifteen steps | 3.75 s within 60 ms |
| | **H_F_whole_sample**: F plays the whole sample | 5.0 s within 100 ms |

Exploratory: patterns 5 to 8, the onset offsets and the session answers.

## Running it

From the repository root, on macOS (on Windows use `.\.venv\Scripts\python.exe`). The build
and the registration are done:

```
cd web && npx tsx scripts/build-aux-nibble-2-test.ts && cd ..
.venv/bin/python -m scripts.prepare_aux_nibble_2_test
```

The session:

```
.venv/bin/python -m po33_re hw run experiments/aux-nibble-002
.venv/bin/python -m scripts.check_aux_nibble_2_test
.venv/bin/python -m scripts.finalize_aux_nibble_2_test
```

1. Cables: the computer's headphone output to the PO-33's input; the PO-33's output
   unplugged. On the PO-33, hold write and press sound + record. `hw run` plays the restore
   (about 2 min).
2. When prompted, swap: unplug the computer's output from the PO-33, connect the PO-33's
   output to the computer's stereo line input. Press write + sound + play when asked; the
   harness records the backup and checks it against the target. If a recording fails to
   decode, let the harness retry; a quiet first take is common on this interface.
3. When asked, press PLAY on the PO-33 and let two full passes play (about 2 min) without
   touching anything, then answer the questions.

- [Registration](../experiments/aux-nibble-registration-002.json)
- [Experiment](../experiments/aux-nibble-002/experiment.json)
