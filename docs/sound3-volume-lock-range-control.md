# Recorded volume minimum and exact loud-state return

Start from the current recorded loud Sound 3 state. No restore is needed. Keep
**Pattern 1 / Sound 3 / TONE**, tempo100, swing9 and knob A untouched. Two recorded
passes will test a candidate in the low four bits of the second primary byte of all
16 Sound 3 cells. No numeric display minimum or maximum is assumed.

The [official guide](https://teenage.engineering/guides/po-33/en), section 6, specifies
WRITE-held knob movement during playback for TONE/FILTER parameter locking.

1. Play Pattern 1. Hold **WRITE**, then slowly turn **only B fully counterclockwise
   over about 5 seconds**. Keep holding WRITE for **3 more seconds**, with knobs
   stationary. Release WRITE, stop playback and ensure write is off. Save a complete
   backup as `experiments/event-045-c-sound3-tone-volume-lock-minimum/capture.wav`.
2. Play again and repeat the same recorded pass, this time turning **only B fully
   clockwise over about 5 seconds**, followed by **3 more seconds holding WRITE**
   with knobs stationary. Release WRITE, stop and ensure write is off. Save
   `experiments/event-046-b-return-sound3-tone-volume-lock-maximum/capture.wav`.
3. Report the quieter/silent behavior at minimum, louder behavior on return and any
   display labels/numbers seen at the endpoints. Leave the recorded maximum in place,
   Sound 3 / TONE selected, stopped and write off.

Save each capture before the next action, using the established reduced levels and
one second trailing silence. No separate ordinary playback recording is required yet.

## Preregistered bitfield test

The original loud endpoint has raw low nibbles `0xf` at concatenated Pattern 1 payload
offsets `48 * step_index + 7`. The test predicts minimum raw values `0x0`, preserving
the first byte's new high bits, second-byte high nibbles, third bytes, all auxiliary
values, other sounds/patterns, samples and global settings. Minimum0 is an encoded
hypothesis, **not** a claimed display reading or promise of silence.

Expected minimum complete body:
`e84321400674817710d81dc3bf8d79b3b9c84b6b02b2d2b490c407c54db1a66b`.
Expected return complete body:
`e34fbe7f6238c230deeacd96139b26e5ca88bb5f300a7831da87a24e32afaef7`.
The return must equal the entire independent earlier loud capture, not merely restore
the candidate nibble. The second leg compares against actual minimum data.

The initial maximum model was found after that capture. These minimum/return
predictions are registered before new data. Another minimum value or an extra changed
bit stays an explicit failed prediction; no new scale or candidate is fitted afterward.
High `0xc0` bits remain opaque, and no volume writer, gain units or mute behavior is
claimed. Missing display readings are never inferred from raw nibbles.

- [Registration](../experiments/sound3-volume-lock-range-registration-001.json)
- [Recorded maximum result](sound3-tone-lock-up-results.md)
- After decoding both captures independently at threshold0.0063:
  `python -m scripts.check_sound3_volume_lock_range`
- Optional `--minimum-display-text` and `--maximum-display-text` preserve actual
  user-reported labels without supplying absent values.

All 14 affected tests pass, covering genuine initial TONE changes and the preregistered
mask, failed alternative minimum, hidden high-bit/auxiliary changes and full return
identity. Production writers remain unchanged.

Completed with a falsified minimum model: all low nibbles reach0, but first-byte0xc0
also clears. The maximum returns exactly. The old failed prediction/report is retained;
see [results](sound3-volume-lock-range-results.md) and the new independently registered
[interior alternatives](sound3-volume-middle-series-control.md). No volume writer is enabled.
