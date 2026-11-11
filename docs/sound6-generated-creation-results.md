# Generated sample creation in empty Sound6 restores exactly

The user reported "done and confirmed" for restoration, the new lower Sound6/key1
tone and unchanged Sound4/Sound5/Pattern1 checks. The hardware recapture passes all951
native checksums with the normal0.0063 acquisition. Its complete native body and every
plain packet match the generated target exactly.

Previously empty Sound6 now has a self-owned32768-code buffer under selector5:
header `00000000c078000005` (start0/end30912/owner5). Every synthesized500Hz tone code
and all1856 zero tail codes survive. All prior sound records, every pattern and every
non-Sound6 plain packet remain identical to the pre-edit baseline. No selector or
opaque global record changed. Total backing capacity is163840 code bytes.

This establishes one generated empty melodic-slot creation using device-derived page
geometry. Along with the verified unshared Sound4 grow/shrink transitions, it supports
bounded sample editing beyond fixed-size replacement. It does not establish arbitrary
slot/capacity support, allocation rounding, memory limits, deletion or shared-owner
mutation. The software report remains `hardware_verified:false`; separate acceptance
combines the manual confirmation with the exact hardware recapture.

- [Exact native comparison](../experiments/edited-sound6-create-001/hardware-recapture-results-001.json)
- [Hardware acceptance](../experiments/edited-sound6-create-001/hardware-acceptance-001.json)
- [User observation](../experiments/edited-sound6-create-001/manual-observation.json)
- [Original registration](../experiments/edited-sound6-create-001/restore-registration.json)
- Current read-only export: `experiments/exported-generated-sound6-create-001/project.json`
- Capture SHA-256: `e21b04a85d73f1f53cb4cbefb1926c17c7f42ab4272c6cce09037a307a8cc776`
- Artifact SHA-256: `51c4a7acb42a604c825c1b4d3ccc581cf0c17d28c96470c0bbc58c2ecfea90ba`
- Native body SHA-256: `258bb81fdb8085ab24f7be4f841ed7ea577a69943ee34a4beccabffd5d9e44f6`

Seven melodic/three calibrated drum previews and all32 export content hashes pass.
Capture peaks0.16827/0.16125 show no clipping and remain consistent with the successful
reduced levels. The next [generated Sound6-to7 copy](sound6-to7-generated-copy-control.md)
creates a retained reference before studying shared-owner deletion.
