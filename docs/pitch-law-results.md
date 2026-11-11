# Pitch-code law confirmed: one semitone per code

The [registered confirmation](pitch-law-control.md) supports one semitone per code. A new
code order was restored through the public plan path and received exactly; measured 50 to
90 ms after each note, after the glide, every step matched within 2.4 cents:

| Code | 1 | 2 | 4 | 5 | 7 | 8 | 10 | 13 | 14 | 16 | 18 | 19 | 21 | 22 | 24 | 25 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Predicted cents | -1200 | -1100 | -900 | -800 | -600 | -500 | -300 | 0 | 100 | 300 | 500 | 600 | 800 | 900 | 1100 | 1200 |
| Measured cents | -1200.1 | -1100.8 | -899.4 | -800.3 | -599.7 | -500.1 | -300.1 | 0.0 | 97.6 | 298.2 | 498.1 | 598.7 | 798.4 | 898.9 | 1099.0 | 1199.0 |

The pitch field therefore spans -12 to +12 semitones around code
13 across the observed range 1 to 25. When the code changes between steps, the note
glides from the previous pitch for about 25 to 35 ms before settling; key changes do not
glide.

Both backups of this run failed the normal decode at the frame start. The left channel
had one extra steady-carrier label at the start; dropping it, with all 815 packet
checksums valid and no target data used, recovered a frame that matches the target
exactly. This leading-label realignment is now an automatic fallback in the harness,
and `hw reanalyze` re-decodes a session's kept backups. See the
[decision](../experiments/pitch-law-confirm-decision-001.json) and
[observation](../experiments/compiled-pitch-law-002/hardware-observation-001.json).
Current genuine export: `experiments/exported-pitch-law-002/project.json`.
