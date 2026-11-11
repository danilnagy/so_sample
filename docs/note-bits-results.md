# Note bits: pitch code 0 is no lock; bit 5 is stored, its effect confounded

The [note bits test](note-bits-control.md) played Sound 1 on every step with pitch codes
including 0, and bit 5 set on three notes. The backup equals the compiled target exactly,
so the device stores bit 5.

## Pitch code 0

`zero_holds_last_pitch` holds on all 16 steps in at least 4 of 5 loops; the alternatives
fail. Each code-0 step played the previous step's pitch within 0.6 cents. Pitch code 0
means no lock, like volume, filter and resonance 0. The pitch field now accepts 0.

## Bit 5

The registered `bit5_inert` model fails: the two flagged pitch-25 notes were 12.5 ms
shorter and 0.7 dB quieter than their plain partners. Pitch matched within 1.2 cents, and
the flagged pitch-13 note matched its partner exactly.

An exploratory look at the first 25 ms explains the failure. The plain partners followed a
pitch change and glided into their pitch, reading 24 to 34 cents off early; the flagged
notes followed a note of the same pitch and started on target. A glide lengthens a note
by about the 12.5 ms measured, and the shorter note in the measurement window also reads
quieter. The design confounded bit 5 with the glide. The
[bit-5 glide test](bit5-glide-control.md) separates them.

- [Registration](../experiments/note-bits-registration-001.json)
- [Decision](../experiments/note-bits-decision-001.json)
- [Observation](../experiments/compiled-note-bits-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-note-bits-001/project.json`
