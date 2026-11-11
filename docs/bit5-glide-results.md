# Bit 5 is inert

The [bit-5 glide test](bit5-glide-control.md) alternated pitch codes 7 and 25 on every
step, with bit 5 clear on the first eight steps and set on the last eight, so every note
followed a pitch change. The backup equals the compiled target exactly.

`bit5_inert` holds and `bit5_no_glide` fails. Flagged and plain notes of the same pitch are
indistinguishable:

| Reading | Pitch 7, plain | Pitch 7, flagged | Pitch 25, plain | Pitch 25, flagged |
| --- | --- | --- | --- | --- |
| Early pitch, cents from target | +68.1 | +69.8 | -25.7 | -25.7 |
| Late pitch, cents from target | +0.2 | +0.2 | -1.2 | -1.2 |
| Level, dB | 32.5 | 32.5 | 26.6 | 26.6 |
| Duration, ms | | | 180.4 | 180.4 |

Every note glided into its pitch whether or not bit 5 was set. The shorter flagged notes
of the [note bits test](note-bits-results.md) were the glide's doing, as suspected.

So bit 5 of a note's primary bytes is stored by the device and changes nothing audible in
pitch, glide, level or length. An editor should leave it clear. Every bit of a note cell
now has a known role or a measured non-effect.

- [Registration](../experiments/bit5-glide-registration-001.json)
- [Decision](../experiments/bit5-glide-decision-001.json)
- [Observation](../experiments/compiled-bit5-glide-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-bit5-glide-001/project.json`
