# Fine 100 BPM uses the same direct tempo byte

The user reported **done, 100** after the requested fine adjustment from the accepted
80 BPM state. All 815 native checksums pass at threshold 0.0063, and the complete native
body equals the preregistered 100 BPM prediction.

Only payload byte 129 (zero-based) in the second `0x7d5c` packet changes 80 to 100. Every
other global byte, sound-parameter packet, sample record, pattern and selector remains
exact. Moving knob B while BPM was held therefore leaves all serialized sound parameters
unchanged in this control. The display value is supplied independently by the user.

This supports one non-preset fine value using the same direct integer mapping. It does
not yet establish the whole range or hardware acceptance of a generated fine tempo.
The public preset writer remains restricted to 80/120/140 and its recognized opaque
context; it rejects 100 as either source or target. The hardware observation records
this narrower physical result without rewriting prior compiler reports.

- [Native comparison](../experiments/event-033-b-fine-tempo-100/native-tempo-results-001.json)
- [Independent user observation](../experiments/event-033-b-fine-tempo-100/manual-observation.json)
- [Hardware association](../experiments/event-033-b-fine-tempo-100/hardware-observation-001.json)
- Current read-only project: `experiments/exported-fine-tempo100-001/project.json`
- Capture SHA-256: `a296fe64000e078997becbc2b9acba5a2a986b6172168658e0cfbe874859ea1b`
- Artifact SHA-256: `b802ea9c8306d5c048ecd95fc629f8c3546a097f1765931b3a49544e96698280`
- Native body SHA-256: `d01d2cdd2f9cd85aca19e17ebc7967327aba647926faf91dcb2db0fe42de2633`

Six melodic and three calibrated drum previews, all 31 export content hashes and the
complete reconstructed native body pass. Capture peaks remain about 0.163 and 0.157,
without clipping. The next [endpoint and return series](fine-tempo-range-series-control.md)
tests 60, 240 and an exact return to this independent 100 state.
