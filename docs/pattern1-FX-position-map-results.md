# Effect position map: sequential, high nibble first

The [registered position map](pattern1-FX-position-map-control.md) supports the
sequential model: **footer byte k holds steps 2k+1 (high nibble) and 2k+2 (low nibble)**.

The restore was received exactly on the first attempt, and the playback passed the
protocol checks. With the footer `FF FF 6F FF FF FF 6F FF`:

| Step | Footer position | Five-loop median | Peak pitch vs reference | Loops agreeing |
| --- | --- | --- | --- | --- |
| 1 | byte 0 high, F | none | 1.000 | 5 of 5 |
| 5 | byte 2 high, 6 | effect | 1.436 | 5 of 5 |
| 9 | byte 4 high, F | none | 1.000 | 5 of 5 |
| 13 | byte 6 high, 6 | effect | 1.436 | 5 of 5 |

The person independently reported that the second and fourth notes bent upward. See
the [decision](../experiments/pattern1-FX-position-map-decision-001.json) and the
[observation](../experiments/edited-pattern1-FX-position-map-001/hardware-observation-001.json).
Current genuine export: `experiments/exported-pattern1-FX-position-map-001/project.json`.

With the byte-0 result, high nibbles of bytes 0, 2, 4 and 6 are now observed on their
predicted steps. Odd bytes and other low nibbles follow the same layout but were not
individually observed. Effect codes other than 6 (rising, known as octave up), 7
(octave down) and F (none) are not yet mapped. No per-step effect writer is enabled.
