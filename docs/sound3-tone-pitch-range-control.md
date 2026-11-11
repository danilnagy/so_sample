# Recorded pitch maximum and exact minimum return

The recorded low-end body has raw candidate value 1 and volume 36 in all 16 Sound 3
cells. This new control registers both next captures before either is collected.
The upper endpoint code is unknown. Returning A to its physical minimum predicts
the entire independent minimum body, not merely matching a few fields.

Keep Pattern 1 / Sound 3 / TONE selected. Leave B and all audio settings unchanged.
The recording action uses the established WRITE-held
[parameter-lock method](https://teenage.engineering/guides/po-33/en), section 6.

1. **Maximum:** start Pattern 1, hold WRITE and slowly turn only A fully clockwise
   over about 5 seconds. Hold WRITE 3 more seconds with both knobs stationary.
   Release WRITE, stop playback, ensure write off, then save a complete backup as
   `experiments/event-052-c-sound3-tone-pitch-lock-up/capture.wav`.
2. Save that maximum backup before beginning the return. **Minimum return:** repeat
   the same action, moving only A fully counterclockwise over about 5 seconds.
   Hold WRITE 3 more seconds stationary, release WRITE, stop and ensure write off.
   Save the complete backup as
   `experiments/event-053-d-return-sound3-tone-pitch-lock-minimum/capture.wav`.
3. Use the established reduced recording level and one second trailing silence
   for both backups. During each pass do not press keyboard keys or hold BPM/FX.
   Report whether pitch went up and back down, plus any display text actually seen.
   Missing numeric readings remain absent. Leave A at minimum and B untouched.

No restore or separate ordinary playback recording is needed for these native range
controls. The expected return body is
`227d4d25e644c83f2d8e89d2a4135125f8cb926082983a81b4842de21e654fc2`.
Both recordings are compared with the registered independent minimum; the entire
return body and packets must match it.

## Predictions and limits

First-low-six-only and narrower first-low-five-only masks are checked separately.
An unchanged sixth bit does not establish field width. Volume 36, sample records,
auxiliary keys, other primary data, other sounds/patterns, globals and packet geometry
have explicit checks. A volume snapshot or wider change remains visible in the
broader TONE alternatives and cannot be called a strict pitch-only result.

Maximum uniformity and raw values are reported literally. A retained ramp is not
averaged or forced into a guessed endpoint. No upper code, semitone law, numeric
display or frequency ratio is inferred before its data. No pitch-field writer or
extension of the public volume context is enabled.

All 45 affected pitch/volume tests pass. They cover genuine minimum/display evidence,
synthetic mixed values, a sixth-bit difference, unchanged upper data, coupled volume,
hidden return changes and stale source hashes. Production code is unchanged in this
control; the last full regression suite passed 853 tests.

- [Preregistration](../experiments/sound3-tone-pitch-range-registration-001.json)
- [Verified minimum](sound3-tone-pitch-minimum-results.md)
- [Range checker](../scripts/check_sound3_tone_pitch_range.py)

After independent decoding of both captures at threshold 0.0063:
`python -m scripts.check_sound3_tone_pitch_range`.
Software reports remain hardware-unverified; user evidence is stored separately.

Completed: high-end data is uniform raw 25, and the complete return equals the
independent raw-1 minimum. Volume 36 and all unrelated state remain exact. See
[results](sound3-tone-pitch-range-results.md) and the next
[generated interior/audio pair](generated-sound3-pitch-pair-control.md).
