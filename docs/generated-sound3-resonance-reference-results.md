# Low-pass16 / B0 reference is accepted and measurable

The new backup independently decodes at threshold0.0063 to815 checksum-valid
packets and end byte156758. Its entire body and every packet equal the generated
reference target:
`ae37ebfdfd485e0e20313c4faeb26065132375c7f0194681fffeda837c6b6264`.
All16 Sound3/Pattern1 cutoff fields are16 and B candidates are0. Pitch14, volume36,
keys, samples and every non-FILTER state bit remain exact. This verifies the new
combined reference context, not just its earlier individually observed endpoints.

The user reports: "done, and confirmed it sounds like the pattern filtered".
This explicitly confirms recognizable filtered-pattern playback after the
requested reference workflow. No remembered amplitude or comparative resonance
strength is inferred.

All six frozen audio measurements pass, with eight fits per channel/threshold.
Median frequencies range530.279993–530.283215Hz, meeting the preregistered530.26Hz
reference gate. Median loops range2.400215–2.400249 seconds. The audio is10.96
seconds long, shorter than the requested12–15-second recording target, but it
passes the unchanged registered minimum-cycle and fit coverage requirements.
No thresholds, windows, search bands or acceptance bounds were changed.

Playback peaks are approximately0.0582/0.0558 full scale; backup peaks are
0.1390/0.1348 without clipping. The established levels remain suitable for the
reference measurement. Current genuine read-only export:
`experiments/exported-sound3-filter16-B0-reference-001/project.json`, with all31
content hashes and complete native reconstruction checked. Raw sample previews
do not render the filtering.

- [Exact native reception report](../experiments/edited-sound3-filter16-B0-reference-001/hardware-recapture-results-001.json)
- [Frozen reference audio report](../experiments/edited-sound3-filter16-B0-reference-001/resonance-frequency-results-001.json)
- [Separate hardware observation](../experiments/edited-sound3-filter16-B0-reference-001/hardware-observation-001.json)
- [User listening confirmation](../experiments/edited-sound3-filter16-B0-reference-001/manual-observation.json)
- [Next B63 candidate action](generated-sound3-resonance-pair-control.md)

The candidate gate now passes. The unchanged prepared B63 waveform is still
software-verified only; its reception and amplitude-increase hypothesis remain
pending. Existing public cutoff guards remain unchanged and no public resonance
writer is enabled. Software reports stay hardware-unverified. Production code
and the prior108 affected /1,025 full regression results are unchanged.
