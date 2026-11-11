# Aux nibble: the high nibble is a drum's retrigger count and a melodic note's length

Session 2026-11-11, [registered design](aux-nibble-control.md). The auxiliary byte of a
pattern cell (`768 + 16*(step-1) + (sound-1)`) holds the key in its low nibble. Its high
nibble, which the app wrote only as F (melodic) and 1 (drum), turns out to set how many
times a drum step retriggers and how many steps a melodic note lasts. The device's own
interface sets both (hold a step and press BPM for a drum's retrigger, turn knob B for a
melodic note's length); this is where they are stored.

| Prediction | Result |
| --- | --- |
| The backup equals the compiled target exactly, raw auxiliary bytes included | **held** |
| H1, drum: nibble n (1, 2, 3, 4, 6, 8) plays n onsets within its step | **held** |
| H0, drum: the nibble has no effect, every probe plays one onset | **failed** |
| H1, melodic: nibble n (1, 2, 4, 8) sounds for n steps (250 ms each, within 60 ms); F and E sound the whole 3 s tone | **held** |
| H0, melodic: the nibble has no effect, every probe sounds the whole tone | **failed** |

## Measurements

60 BPM, so a step is 250 ms; two full passes of the chain were recorded and both gave the
same counts.

| Drum nibble | 1 | 2 | 3 | 4 | 6 | 8 |
| --- | --- | --- | --- | --- | --- | --- |
| Onsets in its step | 1 | 2 | 3 | 4 | 6 | 8 |

| Melodic nibble | 1 | 2 | 4 | 8 | E | F |
| --- | --- | --- | --- | --- | --- | --- |
| Sounded for | 0.26 s | 0.505 s | 1.015 s | 2.005 s | 3.005 s | 3.01 s |

The person running the session heard the same before any analysis: "yes, 1, 2, 3, 4 times"
for the clicks, and tones stopping short of the others.

## Exploratory readings

Not registered as predictions:

- **Retriggers divide the step evenly.** The gaps between repeats were 124 to 126 ms for 2,
  84 ms for 3, 60 to 64 ms for 4, 40 to 44 ms for 6 and 30 to 32 ms for 8, that is step/n
  within the 2 ms measurement hop, in both passes.
- **Off-cycle drum nibbles round up.** Nibble 5 played 6 onsets and 7 played 8, at the same
  spacing as 6 and 8: the device's cycle is 1, 2, 3, 4, 6, 8, and a value between steps of
  it plays as the next.

## What this establishes

- A drum note's auxiliary high nibble is its retrigger count, 1, 2, 3, 4, 6 or 8 (1 is a
  single hit, as the app writes).
- A melodic note's auxiliary high nibble is its length in steps, at least for 1, 2, 4 and
  8; a note shorter than its sample is cut at that length. F and E both outlasted the 3 s
  tone (E would be 3.5 s), so the session cannot tell whether F means 15 steps or
  "sustain to the end of the sample".
- The earlier [stray bits](stray-bits-results.md) reading ("the high nibble does not select
  a note type", write only F and 1) stands as far as it went: F and 1 remain the right
  defaults for a full-length note and a single hit. That test could not hear length (its
  tone ended within the step) and put no other nibble on a drum.

## Limits

- One session on one device.
- Melodic nibbles 3, 5, 6, 7 and 9 to D, and the meaning of F against E, were not measured;
  "n steps" is the registered rule for 1, 2, 4 and 8 only.
- Onset counting assumes repeats at least 12 ms apart; at 60 BPM the closest were 30 ms. At
  higher tempos an 8-fold retrigger is faster (about 16 ms at 120 BPM) and was not measured.
- How retrigger and length interact with effects, parameter locks and swing was not tested.
- The backup was decoded on its second recording, at detection threshold 0.01 rather than
  the default 0.0063: the first recording was too quiet, and the second failed the first
  packet's checksum at the default threshold, most likely from noise before the transfer.
  The re-decode is recorded in `hardware-session-002.json`, and it matched the target
  exactly.

## For the app

The app writes and previews both (2026-11-11): a Len or Rpt lane and parameter-row choice
edits a note's timing, F and 1 stay the defaults, and the preview follows the rules of this
session and [aux nibble 2](aux-nibble-2-results.md) and [3](aux-nibble-3-results.md)
([web playback](web-playback.md)).

- [Registration](../experiments/aux-nibble-registration-001.json)
- [Decision](../experiments/aux-nibble-decision-001.json)
- [Observation](../experiments/aux-nibble-001/hardware-observation-001.json)
