# Generated 137 BPM restore verifies fine-tempo editing

The user reported **done and confirmed**, confirming the requested restore checks:
the expected 137 display, same Pattern1 phrase at the new tempo and unchanged samples.
The observation records confirmation of the prior numeric expectation, not a separately
typed number or a display reading inferred from backup bytes.

All 815 checksums pass at threshold 0.0063. The complete recapture equals the supplied
137 target; only second `0x7d5c` payload byte 129 changes100 to137. Every other global byte,
sound parameter, sample, pattern and selector remains exact. This was a previously
unobserved fine target, rather than a replay of an existing physical 137 capture.

Guarded [integer tempo editing](tempo-edits.md) from 60 to 240 is now available. That
range policy combines the documented device range, physical 60/240 endpoints,
representative preset/fine values and generated 80/137 restores. It does not claim
individual hardware tests for every integer. Unknown global contexts remain rejected.

The source-bound `experiments/replay-fine-tempo 137-plan-001/plan.json` compiles into
`experiments/compiled-fine-tempo 137-plan-001/restore.wav`, byte-identical to the accepted
WAV. Original research and replay compiler reports remain software-only; acceptance is
separate and immutable.

- [Native recapture](../experiments/edited-fine-tempo 137-001/hardware-recapture-results-001.json)
- [Hardware acceptance](../experiments/edited-fine-tempo 137-001/hardware-acceptance-001.json)
- [User confirmation](../experiments/edited-fine-tempo 137-001/manual-observation.json)
- Current read-only project: `experiments/exported-generated-fine137-001/project.json`
- Capture SHA-256: `0538c163106bac0f0c9ac88471ab246c3c53dc713db60c86233eed68e87e9a13`
- Artifact SHA-256: `c5b3375847b325fc70ffc558e4a4aa49f39bef919e3f312c23d251fb877d609b`
- Body SHA-256: `5f25b5efd909c93b0aa0cdbb31d8aff170ea5edeb9ca6dd48eb2d7778ae696cb`
- Accepted/replayed WAV SHA-256: `8594f6930ee6ef709caba0620381de47999532ab86d0c7ed98d1f245d31816c7`

All 31 exported content hashes and complete-body reconstruction pass; peaks are about
0.163 and 0.156 without clipping. The next [swing control](swing-max-control.md) fixes
tempo 137 while testing another field. The full regression suite passes 740 tests.
