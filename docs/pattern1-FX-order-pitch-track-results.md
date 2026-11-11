# Effect order confirmed: footer high nibble is the earlier step

The [registered pitch-track confirmation](pattern1-FX-order-pitch-track-control.md)
supports **high nibble first** for Pattern 1 footer byte 0.

Both fresh restores were received exactly on the first attempt. Only footer byte 0
differs from the single-tone source, and global byte 131 stays 7. Both playback
recordings passed the harness protocol checks. Restore B's first playback attempt was
rejected because the sound started at once, and its retry was used.

| Restore | Footer byte 0 | Step 1, five-loop median | Loops agreeing |
| --- | --- | --- | --- |
| A | F6 | none: pitch stays at 1.000 times the 1190.417 Hz reference | 5 of 5 |
| B | 6F | effect: pitch rises to 1.29 times the reference | 5 of 5 |

Only the high-nibble-first prediction matches. In footer byte 0, the high nibble holds
step 1's effect and the low nibble holds step 2's. Effect code 6 fades in over its step:
the pitch rises through the step rather than jumping an octave. The person described
both playbacks as a "pitch bend at beginning".

The method was frozen by file hash and settings before these recordings. It was
developed on the earlier -001 recordings, which are not counted. See the
[decision](../experiments/pattern1-single-tone-FX-order-pitch-track-decision-001.json),
[registration](../experiments/pattern1-single-tone-FX-order-pitch-track-registration-001.json)
and the leg observations in each experiment folder. Current genuine exports:
`experiments/exported-pattern1-single-tone-FX-F6-002/project.json` and
`experiments/exported-pattern1-single-tone-FX-6F-002/project.json`.

This is local to footer byte 0 of Pattern 1. The earlier mixed-halves result showed
bytes 0 to 3 cover the first half of the pattern and bytes 4 to 7 the second. The exact
step position of the other bytes, and other effect codes, are not yet confirmed. No
per-step effect writer is enabled.
