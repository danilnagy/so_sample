# Per-step effect writer: hardware verified

The [registered writer test](step-effects-writer-control.md) passed. A plan compiled
through the public `apply-edits` path with `set_step_effects` put FX key 7 on steps 1, 4,
7, 8, 9, 12, 15 and 16 of Pattern 1. The backup matched the compiled target exactly, and
the frozen per-note-gate method classified every step as the sequential layout predicts,
five of five loops each:

| Steps | Classified | Peak pitch vs reference |
| --- | --- | --- |
| 4, 7, 12, 15: effect after a step without it | effect | 1.43, the crossfade |
| 1, 8, 9, 16: effect after a step with it | effect | 2.00, the full octave |
| 2, 3, 5, 6, 10, 11, 13, 14 | none | 1.00 |

Step 1 reads a full octave because step 16 before it, across the loop boundary, also
carries the effect. Together with the [code map](FX-code-map-results.md), this verifies
the complete per-step effect encoding: footer byte k holds step 2k+1 in its high nibble
and step 2k+2 in its low nibble, each storing FX key - 1, with F for none.

`set_step_effects` is hardware verified for this plan path. Its scope is all 16 patterns
and FX keys 1 to 15, based on the identical footer layout and the device-recorded codes;
the sound of keys other than 7 was not measured. See the
[decision](../experiments/step-effects-writer-decision-001.json) and
[observation](../experiments/compiled-step-effects-writer-001/hardware-observation-001.json).
Current genuine export: `experiments/exported-step-effects-writer-001/project.json`.
