# Single-tone effect order: results

Both [registered restores](pattern1-single-tone-FX-order-control.md) were received
exactly on the first attempt. Each backup matches its target body and every packet.
Only footer byte 0 differs from the single-tone source, and global byte 131 stays 7.
Both playback recordings passed the harness protocol checks.

## Registered result: inconclusive

| Restore | Footer byte 0 | First tone under the frozen method |
| --- | --- | --- |
| A | F6 | 1190.41 Hz in all six measurements, fit 0.99999 |
| B | 6F | Unusable: dominant pitch near 1565 Hz, fit 0.07 |

No A/B ratio could be formed, so neither model is supported, and the reference
cross-check is not reached. The comparison is kept unchanged. The earlier first-pair
B leg failed the same way, near 1567.5 Hz with fit 0.068. See the
[comparison](../experiments/pattern1-single-tone-FX-order-comparison-001.json).

## Exploratory reading: the effect fades in, and step 1 is the high nibble

The frozen method assumes a steady tone. The person reports that the effect "fades in"
on its step, and described both playbacks as bending. A pitch track written after the
registered result, so exploratory only, shows the median pitch over five loops:

| Time after onset | No effect | A, F6 | B, 6F |
| --- | --- | --- | --- |
| 0 to 140 ms, step 1 | 1190 Hz | 1190 Hz | rising 1214 to 1665 Hz |
| 160 to 200 ms, step 2 | 1190 Hz | rising 1245 to 1371 Hz | near 1200 Hz |

Steps last 150 ms at 100 BPM, and the note fades out at about 210 ms. In both restores
the effect sits where the footer's **high nibble** places it on step 1 and the low nibble
on step 2. F6 means step 1 none and step 2 up; 6F means step 1 up and step 2 none. The
effect ramps upward within its step instead of jumping a full octave, which explains
both failed steady-tone measurements. See the
[pitch tracks](../experiments/pattern1-single-tone-FX-order-pitch-track-exploratory-001.json)
and [script](../scripts/pattern1_fx_pitch_track_exploratory.py).

This agrees with the unregistered lead from the first pair. It remains exploratory until
a time-resolved method is registered and tested on fresh recordings. No per-step effect
writer is enabled. Current genuine exports:
`experiments/exported-pattern1-single-tone-FX-F6-001/project.json` and
`experiments/exported-pattern1-single-tone-FX-6F-001/project.json`.
