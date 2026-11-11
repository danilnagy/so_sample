# Recorded TONE pitch down isolates the candidate bits

The new capture decodes independently at threshold 0.0063 to 815 checksum-valid
packets and end byte 156758. Its complete body is
`227d4d25e644c83f2d8e89d2a4135125f8cb926082983a81b4842de21e654fc2`.
The registered strict pitch-candidate location passes: only first-primary low-six
bits in Sound 3 / Pattern 1 change. All samples, other sounds, other 15 patterns,
globals 100/9, keys, other primary bits and footer remain exact. Volume stays 36
in all 16 cells.

All 16 first-low-six candidate values are now 1. The five existing note tuples
change from `0df983` to `01f983`; the 11 parameter-only tuples change from `000900`
to `010900`. Auxiliary values remain literal, so no new-note interpretation is
imposed. The observed differing bits are first-byte 0/2/3; this does not prove
that the candidate occupies all six bits.

The user explicitly reports lower pitch, "Ptc" in the upper right, and ticks
along the bottom "descreasing to right". The exact message is preserved in the
manual observation. No numeric display value was supplied; stored raw 1 is not
called a UI reading or a semitone value.

A separate post-observation literal model sets first-low-six values to 1 and
reproduces the entire actual body. That rule was formed after this capture and
does not become a retroactive endpoint prediction. Broader location flags in the
original report include the strict mask as nested alternatives; their true values
do not imply that other bits or auxiliary bytes changed.

Backup peaks approximately 0.156/0.150 remain suitable. All 31 content hashes and
native reconstruction checks pass for the genuine read-only export:
`experiments/exported-sound3-tone-pitch-minimum-001/project.json`.
Raw sample previews preserve codes and do not render the pattern pitch shift.
The existing public volume writer correctly rejects this changed-pitch context.

- [Immutable probe checks](../experiments/event-051-b-sound3-tone-pitch-lock-down/pitch-probe-results-001.json)
- [Manual report](../experiments/event-051-b-sound3-tone-pitch-lock-down/manual-observation.json)
- [Hardware observation](../experiments/event-051-b-sound3-tone-pitch-lock-down/hardware-observation-001.json)
- [Post-observation literal model](../experiments/event-051-b-sound3-tone-pitch-lock-down/minimum-post-observation-model-001.json)

The [next maximum/minimum-return control](sound3-tone-pitch-range-control.md)
registers an unknown upper endpoint and an exact return to this independent body.
No pitch scale, definite field width, frequency ratio or pitch-field writer is enabled.
