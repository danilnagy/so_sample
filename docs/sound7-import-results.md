# Sample import into Sound 7: hardware verified

The [registered test](sound7-import-control.md) passed. A 600 Hz tone imported into empty
Sound 7 (32768-code capacity, owner byte 6) was received exactly, every imported code
included. In playback, every Sound 7 note measured -386.3 to -386.4 cents relative to
Sound 3, against the predicted -386.3, in all five loops. The person heard every other
note lower.

Sound 3's notes measured 1123.85 Hz. Its stored tone is 750.0 Hz, and the rule "key 1 at
pitch code 13 plays stored audio 7 semitones up" predicts 750 x 2^(7/12) = 1123.7 Hz,
within 0.2 cents. Together with the pitch-code and key layouts, a note's pitch is now
predictable from the stored audio:

    playback frequency = stored frequency x 2^((7 + key offset + (pitch code - 13)) / 12)

where the key offset comes from the confirmed row layout (0 for key 1).

The public importer now accepts Sound 6 and Sound 7. Other melodic slots currently hold
samples or references to Sound 1's buffer and are not import targets yet. See the
[decision](../experiments/sound7-import-decision-001.json) and
[observation](../experiments/compiled-sound7-import-001/hardware-observation-001.json).
Current genuine export: `experiments/exported-sound7-import-001/project.json`.
