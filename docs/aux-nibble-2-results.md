# Aux nibble 2: retriggers re-strike one voice and restart; F plays the whole sample

Session 2026-11-11, [registered design](aux-nibble-2-control.md), following
[aux nibble](aux-nibble-results.md). At 60 BPM (a step is 250 ms), no swing. The backup
equalled the compiled target exactly on its first recording.

| Prediction | Result |
| --- | --- |
| Reception: the backup equals the target exactly | **held** |
| H1_one_voice: a drum retriggered 4 times plays 4 onsets whether 0, 1, 2 or 3 other voices are held | **held** |
| H2_voice_per_repeat: each repeat needs a voice, so 4, 3, 2, 1 onsets | **failed** |
| H1_restart: each repeat restarts the drum; the body after the 4th repeat matches a single hit (0 dB, within 1.5) | **held** |
| H2_overlap: repeats sound on over each other (about +4 dB) | **failed** |
| H_holders_continue: the held tones are not cut by the retriggers (2.0 s each, within 60 ms) | **held** |
| H_length_steps: melodic nibbles 3, 5, 6, 7 and 9 to E last n steps | **held** |
| H_F_15_steps: F lasts 15 steps (3.75 s) | **failed** |
| H_F_whole_sample: F plays the whole 5 s sample | **held** |

## Measurements

Two passes, the same each time.

| Voices held by other sounds | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| Onsets of the 4-fold retrigger | 4 | 4 | 4 | 4 |

The body power 12 to 52 ms after the fourth repeat was 0.82 dB above a single hit's;
overlapping copies would have added about 4.07 dB. Each held tone sounded 2.01 s.

| Melodic nibble | 3 | 5 | 6 | 7 | 9 | A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sounded for (s) | 0.76 | 1.26 | 1.51 | 1.76 | 2.26 | 2.51 | 2.76 | 3.01 | 3.26 | 3.51 | 5.01 |

Each is n × 250 ms plus 10 ms; F ran to the end of the 5 s sample.

## Exploratory readings

- **FX 13 over a retriggered drum** (held from step 1) left the burst as it was: four
  clicks 62 ms apart.
- **FX 14** held from step 5 replayed the retriggered burst at 1 s and 2 s, four clicks each
  time, as it replays any earlier steps ([FX reference](fx-reference.md)).
- **FX 13 over a 2-step melodic note** sounded one stretch of 0.67 s, longer than the note's
  0.5 s; **FX 14** replayed the 0.5 s note twice.

## What this establishes

- A drum note's retriggers use the one voice the note took: they never need another voice
  and never drop for want of one, and they do not cut other sounds' notes.
- Each repeat restarts the sample; the earlier repeat stops rather than sounding on.
- A melodic note's nibble n, for every n from 1 to E, lasts n steps; F plays the sample to
  its end, however long. F is "full length", not 15 steps.

## Limits

- One session, one device, 60 BPM, no swing (tempo and swing: [aux nibble 3](aux-nibble-3-results.md)).
- Voice use was tested with retrigger 4 on one drum sound against melodic holders; other
  counts, drum-against-drum and voice-priority interactions were not.
- The choke reading compares body power in one window; it shows a restart, not the exact
  shape of the cut.
- No observations beyond "same" (the bursts sounded alike with and without held tones) and
  "yes" (the tones stopped at different times) were noted.

- [Registration](../experiments/aux-nibble-registration-002.json)
- [Decision](../experiments/aux-nibble-decision-002.json)
- [Observation](../experiments/aux-nibble-002/hardware-observation-001.json)
