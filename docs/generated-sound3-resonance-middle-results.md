# Raw B32 is accepted and between both measured endpoints

Independent threshold0.0063 decoding recovers815 valid packets and end byte156758.
The entire native body and every packet match the generated B32 target
`d039d344987f852ad3a8668249fab8a1366e1d1e9bc9280c789d0059947ca73f`.
Only third-primary bits2..7 differ from the accepted B63 source. Cutoff16, pitch14,
volume36, auxiliary keys, samples and every unrelated state bit remain exact.

Both preregistered amplitude comparisons pass in all six measurements. Middle/B0
ratios range6.466992–6.469474; B63/middle ratios range1.104780–1.104795. The middle
tone component is therefore between the observed endpoints with both registered
5% margins. This is not a linear or proportional resonance scale: raw32's measured
component is much closer to the maximum than the minimum. No general all-code law
or bit7's complete role is inferred.

Median frequencies range530.215936–530.216113Hz and loops2.400499–2.400522 seconds,
within the unchanged consistency limits. The22.90-second playback uses18 fits per
channel/threshold under the same frozen method, with no truncation or refitting.
Backup peaks are0.1380/0.1349 and playback peaks0.1193/0.1142 full scale, without
clipping. The established levels remain suitable.

The user reports: "done and confirmed I can still hear the pattern". This confirms
audibility without inventing a subjective ranking of resonance strength. The
between-endpoint result comes from separate frozen measurements.

Current genuine read-only export:
`experiments/exported-sound3-filter16-B32-middle-001/project.json`; all31 content
hashes and complete native reconstruction pass. Raw previews do not render the
parameter effects.

- [Native reception](../experiments/edited-sound3-filter16-B32-middle-001/hardware-recapture-results-001.json)
- [Frozen two-sided comparison](../experiments/edited-sound3-filter16-B32-middle-001/middle-audio-comparison-results-001.json)
- [Hardware observation](../experiments/edited-sound3-filter16-B32-middle-001/hardware-observation-001.json)
- [Exact user confirmation](../experiments/edited-sound3-filter16-B32-middle-001/manual-observation.json)
- [Guarded public resonance plans](sound3-resonance-edits.md)
- [Next saved-FX probe](pattern1-FX-probe-control.md)

All1,137 regression tests pass, including29 new public resonance checks. A further42
FX/resonance checks pass after the full run with no later production changes.
Public editing is restricted to the three observed raw codes at fixed cutoff16;
earlier cutoff/pitch/volume guards remain unchanged. Software reports remain
hardware-unverified and physical evidence stays separate.
