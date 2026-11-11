# Recorded B minimum clears third-primary bit7

Independent threshold0.0063 decoding recovers815 checksum-valid packets and end
byte156758. Only third-primary bit7 clears in Sound3/Pattern1 note steps1/2/5/9/13.
Their tuples change from `0ef983` to `0ef903`, matching the existing parameter-only
tuples. Auxiliary keys, pitch14, volume36, cutoff63 and every other state bit remain
exact. Body SHA-256:
`bee177abf44962fde6bee1279572df70c7f0b5cf87ffadc51ffaae4768d3d274`.

The preregistered0xfc candidate fits the changed bits and full preservation scope.
The narrower0x7c mask fails because it excludes the actual bit7 change; its changed
step list is empty. Both raw projections now read0 in all16 cells. Before this
pass, the narrow projection was already0 everywhere, while the six-bit projection
was32 at the five notes and0 elsewhere. Only bit7 is exercised here, so this does
not establish the complete field width, lower-bit behavior or bit7's general role.
The failed narrower result remains in the immutable report.

The user reports: "done, no audible change, explainable with no filter". No audible
change is explicit. Neutral cutoff as its cause is a user explanation consistent
with stored63, not a measured resonance response. No numeric UI, digital silence,
zero-as-mute rule or complete resonance law is inferred.

A literal six-bit-zero model reproduces the whole body, but it was written after
observing the data;0 was not a prior endpoint prediction. Capture peaks are
approximately0.1415 and0.1372 full scale without clipping. The reduced recording
level remains suitable. Current genuine read-only export:
`experiments/exported-sound3-filter-B-minimum-001/project.json`; all31 hashes and
complete native reconstruction pass. Raw previews do not render parameter effects.

- [Native report and retained narrow-mask failure](../experiments/event-062-a-sound3-filter-B-lock-down/B-probe-results-001.json)
- [Separate hardware observation](../experiments/event-062-a-sound3-filter-B-lock-down/hardware-observation-001.json)
- [Exact user report](../experiments/event-062-a-sound3-filter-B-lock-down/manual-observation.json)
- [Post-observation literal model](../experiments/sound3-filter-B-minimum-post-observation-model-001.json)
- [Next unknown maximum and exact minimum return](sound3-filter-B-range-control.md)

The existing public cutoff editor correctly rejects this newly changed third-byte
layout. Its guards remain unchanged and no resonance writer is enabled. All82
affected checks pass; production code is unchanged since the full1,025-test run.
Software reports remain hardware-unverified and physical observations separate.
