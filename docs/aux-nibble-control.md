# Aux-nibble test: note length and drum retrigger

Registered 2026-11-11. A step's auxiliary byte holds the note's key in its low nibble; the
app writes F in the high nibble for a melodic note and 1 for a drum note
([format reference](format-reference.md)). [Stray bits](stray-bits-results.md) found that
other high nibbles still play as notes, but it put no other nibble on a drum and its melodic
tone may have ended within the step. The device's interface sets a melodic note's length
(hold a step, turn knob B) and a drum step's retrigger count (hold a step, press BPM: 1, 2,
3, 4, 6, 8), and other work associates both with this nibble
([prior art](prior-art.md#open-question-note-length-and-drum-retrigger)). This session asks
the device directly, with sounds chosen so both effects are measurable.

## Build

`web/scripts/build-aux-nibble-test.ts` compiles a project at 60 BPM (a step is 250 ms) from
the empty-device template with two generated samples: a 12 ms click (a 3 kHz burst
decaying in 4 ms) on Sound 9 key 1, and a 3 s 500 Hz tone on Sound 1 key 5 (its own
pitch). It writes each probe's auxiliary byte raw, asserts that every byte reaches the
compiled patterns as written and that no other cell holds a note, and writes `restore.wav`,
`packets.json` and `project.json` into `experiments/aux-nibble-001`.
`scripts/prepare_aux_nibble_test.py` decodes that restore with the Python decoder into the
expected artifact, requires the packets to equal the compiler's, pins the measurement method
by hash, and registers the predictions below.

## Probes

Chain 1 to 10, one bar each, 40 s a pass.

| Pattern | Steps | Sound | High nibbles (aux bytes) |
| --- | --- | --- | --- |
| 1 | 1, 9 | 9 key 1 (click) | 1, 2 (0x10, 0x20) |
| 2 | 1, 9 | 9 key 1 | 3, 4 |
| 3 | 1, 9 | 9 key 1 | 6, 8 |
| 4 | 1, 9 | 9 key 1 | 5, 7 (outside the interface's cycle) |
| 5 to 10 | 1 | 1 key 5 (tone) | F, 1, 2, 4, 8, E (0xF4, 0x14, ...) |

Drum probes sit eight steps apart, so a retrigger that lasted a step per count could not
reach the next probe; each tone has a 4 s bar to itself, longer than the tone.

## Predictions

Registered in `experiments/aux-nibble-registration-001.json` before the session:

1. **Reception.** The backup equals the compiled target exactly, raw auxiliary bytes
   included.
2. **H1, drum retrigger.** A drum step with nibble n in 1, 2, 3, 4, 6, 8 plays n onsets
   within its own step.
3. **H0, drum.** The nibble has no audible effect: every drum probe plays one onset.
4. **H1, melodic length.** A melodic note with nibble n in 1, 2, 4, 8 sounds for n steps
   (within 60 ms); F and E sound the whole 3 s tone.
5. **H0, melodic.** Every melodic probe sounds the whole tone (within 100 ms).

H1 and H0 exclude each other for each sound; if neither holds, the result is "neither",
recorded with its measurements, and no rule is adopted. Nibbles 5 and 7 on the drum, the
onsets over the eight steps after each drum probe, and the session answers are exploratory.

## Method

`scripts/aux_nibble_method.py`, frozen by hash: band-pass the playback around the click
(2 to 4.5 kHz) and the tone (380 to 650 Hz); count click onsets on a 2 ms envelope (rising
past 30% of the loudest click after falling below 10%, at least 12 ms apart), anchored on
each probe's first onset; measure each tone from its onset to its first fall below a tenth
of its peak on a 10 ms envelope. Every full pass of the chain in the recording is measured
and each prediction decided by majority over passes. `tests/test_aux_nibble_method.py`
checks the method on synthetic playbacks of H1, of H0 and of a third rule that must fail
both, with a 0.02% clock drift.

## Running it

From the repository root, on macOS (on Windows use `.\.venv\Scripts\python.exe`):

```
cd web && npx tsx scripts/build-aux-nibble-test.ts && cd ..
.venv/bin/python -m scripts.prepare_aux_nibble_test
.venv/bin/python -m po33_re hw run experiments/aux-nibble-001
.venv/bin/python -m scripts.check_aux_nibble_test
.venv/bin/python -m scripts.finalize_aux_nibble_test
```

The first two lines are done: the restore is built and the test registered. `po33 hw run`
plays the restore (computer output to the PO-33 input, its output unplugged), prompts for
the cable swap, records the backup and checks it against the target, then records 90 s of
playback (PLAY on the device; two full passes) and asks the observation questions. The check
writes the native result, the measurements and `experiments/aux-nibble-decision-001.json`;
the finalize step records the observation, failed predictions included. The results document
is written from the decision after the session.

- [Registration](../experiments/aux-nibble-registration-001.json)
- [Experiment](../experiments/aux-nibble-001/experiment.json)
