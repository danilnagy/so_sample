# Generated Sound4 shrink restores exactly

The user reported "done and confirmed" for restoration and the requested Sound4,
Sound5 and Pattern1 checks. The supplied hardware recapture passes all815 native
checksums under the normal0.0063 acquisition. Its entire native body and every plain
packet match the generated shrink target exactly.

Sound4's backing capacity falls from73728 to32768 code bytes. Its header is
`00000000c078000003` (start0/end30912/owner3). Every generated2250Hz tone code and all1856
zero tail codes survive. Sound5's entire independently owned buffer, all other sounds,
all16 patterns and every non-Sound4 plain packet remain unchanged.

Both observed unshared Sound4 transitions now have separate hardware evidence:
32768/end30912 to73728/end72128 and back. They reuse literal device-derived layouts;
this does not establish a general capacity-selection rule or arbitrary owner support.
The software report stays `hardware_verified:false`, with a separate acceptance
report for the manual result and exact recapture.

- [Exact native comparison](../experiments/edited-sound4-shrink-001/hardware-recapture-results-001.json)
- [Hardware acceptance](../experiments/edited-sound4-shrink-001/hardware-acceptance-001.json)
- [User observation](../experiments/edited-sound4-shrink-001/manual-observation.json)
- [Original registration](../experiments/edited-sound4-shrink-001/restore-registration.json)
- Current read-only export: `experiments/exported-generated-sound4-shrink-001/project.json`
- Capture SHA-256: `4a11f64a99e10c2a6d49bcd3a1e4c4c5a2cc43ab481d1b884e396921b34fb3c5`
- Artifact SHA-256: `066cc3321f53582a051456dbd771f13253a3a13fc22e8c15ec8aa3e08590643f`
- Native body SHA-256: `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0`

All31 export content hashes pass, including six melodic and three calibrated drum
previews plus exact source/raw records. The next [empty Sound6 creation](sound6-generated-creation-control.md)
tests populating an existing empty selector with a new independently owned sample.
