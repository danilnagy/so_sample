# Fixed low-pass16 B0/B63 pair supports a resonance effect

The B63 candidate independently decodes at threshold0.0063 to815 checksum-valid
packets and end byte156758. Its entire body and every packet match target
`fd0817c1c7791225eab3fe2f2d91f459ddad0c00fd0aacbd87e8672232323039`.
Both accepted pair bodies differ only in third-primary bits2..7. Cutoff16, pitch14,
volume36, keys, samples and every other state bit remain exact.

All six frozen amplitude-increase hypotheses pass. The repeated tone component
has candidate/reference amplitude ratios7.144626–7.147395. Median candidate
frequencies are530.251653–530.252139Hz; relative frequency differences from the
reference are below0.006%, and loop differences are below0.125ms. The candidate's
median loop is2.400340 seconds. These results support the functional resonance
interpretation at fixed cutoff16, not a whole-sample loudness ratio, broadband
response or all-code resonance law.

The user reports: "done, confirmed this version sounds like it has more resonance
or filter effect". This explicitly supports a stronger perceived effect, retaining
the user's alternative wording. Native reception, listening and measured component
amplitude are separate evidence. No numeric UI value is inferred.

The22.20-second candidate playback is longer than the requested12–15-second target.
The unchanged method uses all17 usable fits per channel/threshold, compared with
eight in the10.96-second reference. No truncation, thresholds, windows, frequency
search or acceptance bounds were changed to obtain a pass. Candidate playback
peaks are approximately0.1734/0.1659 full scale; backup peaks are0.1371/0.1332,
without clipping. Established recording levels remain suitable.

Current genuine read-only export:
`experiments/exported-sound3-filter16-B63-candidate-001/project.json`, with all31
content hashes and complete native reconstruction checked. Raw previews do not
render the parameter effects.

- [Frozen pair audio comparison](../experiments/sound3-generated-B0-B63-audio-results-001.json)
- [Candidate native reception](../experiments/edited-sound3-filter16-B63-candidate-001/hardware-recapture-results-001.json)
- [Candidate hardware observation](../experiments/edited-sound3-filter16-B63-candidate-001/hardware-observation-001.json)
- [Exact listening report](../experiments/edited-sound3-filter16-B63-candidate-001/manual-observation.json)
- [Reference results](generated-sound3-resonance-reference-results.md)
- [Next raw32 interior test](generated-sound3-resonance-middle-control.md)

All110 affected checks pass; production code is unchanged since the full1,025-test
run. The next B32 target and between-endpoint component-amplitude hypothesis are
registered after these endpoint results and before middle data. Existing public
cutoff guards remain unchanged; no public resonance writer or complete bit7
semantics is enabled. Software reports remain hardware-unverified and physical
evidence stays separate.
