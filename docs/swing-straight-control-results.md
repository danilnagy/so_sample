# Generated straight offbeat control

The user reported **“done, confirmed I can hear it”**, confirming the requested restore
and added Step 2 note. No swing display was independently reported or inferred.

The new backup independently decodes at threshold 0.0063 to 815 checksum-valid packets,
ending at byte 156758. Its complete native body and every plain packet exactly match
the registered straight target:
`1da3b29b71a0ce601b485b94a5b40256058d3cf79f61d50f743d25fe28aa03e2`.
Tempo is 137, the stored swing byte is 0, and the only pattern change is the exact
copied Sound 3/key 16 event from Step 13 to Step 2. All samples and other fields remain
unchanged. This verifies the generated straight control, not the positive swing probe.

The separate ordinary playback is 28.270 seconds long. The repeated note component
is approximately 500.65 Hz, correcting the earlier **high-note** description. The
original pair registration is retained unchanged. A separate measurement registration
records this correction and fixes the tone band and tolerances using only straight
data, before any swing-6 backup or playback exists.

Both channels resolve 29 usable onsets, or 14 complete cycles. At the 25% envelope
threshold, median gaps are:

| Measurement | Seconds |
| --- | --- |
| Short, Step 13 to next Step 2 | 0.547778 |
| Long, Step 2 to Step 13 | 1.203946 |
| Whole loop | 1.751723 |

These match the expected 5/16 and 11/16 fractions of a straight loop and the nominal
137 BPM period of 1.751825 seconds. All three thresholds (15%, 25%, 35% of the band
envelope peak) agree in both channels. Maximum gap residual is below 1.66 ms; threshold
dependence is below 0.5 ms. Absolute onset times include filtering and threshold delay,
so future comparison uses intervals from the same note and fixed measurement method.
This does not assign percent or clock units to the swing byte.

The immutable [hardware observation](../experiments/edited-swing-timing0-001/hardware-observation-001.json)
binds user confirmation, original WAVs, native recapture, timing report and export.
Compiler and analysis reports remain hardware-unverified. The current genuine export is
`experiments/exported-swing-timing0-001/project.json`; all 31 content hashes and complete
native-body reconstruction pass.

All 47 affected tests pass, including independent synthetic 35 ms offbeat delays at
44.1/48 kHz, rejection of unchanged timing and tempo changes, insufficient-cycle refusal,
fixed-parameter enforcement, actual stereo playback and earlier packet controls.

- [Exact backup results](../experiments/edited-swing-timing0-001/hardware-recapture-results-001.json)
- [Straight timing results](../experiments/edited-swing-timing0-001/playback-timing-results-001.json)
- [Frozen measurement registration](../experiments/swing-timing-measurement-registration-001.json)
- [Next swing-6 action](swing-timing-pair-control.md)

The swing-6 restore is already prepared and software checked. Its identical pattern
should produce a longer short gap and a shorter long gap, with the same whole loop.
Hardware acceptance and audible timing remain pending; no public swing writer is enabled.
