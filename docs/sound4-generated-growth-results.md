# Generated Sound4 growth restores exactly

The first generated allocation-growth backup is accepted on the PO-33. The user
confirmed the restore and requested Sound4, Sound5 and Pattern1 checks, then supplied
the hardware recapture. Normal0.0063 acquisition passes all985 native checksums.

The entire recaptured native body and every plain packet match the generated target
exactly. Sound4's capacity grew from32768 to73728 code bytes; its header is
`00000000c019010003` (start0/end72128/owner3). Every synthesized sample code, including
the1600 zero tail codes, survived. Sound5's full independent buffer and header,
every other sound and all16 patterns remain byte-identical to the pre-edit baseline.

The generated1750Hz tone spans about3.08seconds at the nominal rate. The audible checks
are user confirmations; the packet comparison independently verifies exact retained
codes and state. No separate device playback recording was supplied.

This establishes one bounded unshared Sound4 growth using an independently observed
device layout. It does not establish allocation rounding, arbitrary capacities,
other owners, creation/deletion, memory limits or shared-owner resizing. The immutable
software report stays `hardware_verified:false`; separate hardware acceptance records
the completed manual test and matching recapture.

- [Exact recapture comparison](../experiments/edited-sound4-growth-001/hardware-recapture-results-001.json)
- [Hardware acceptance](../experiments/edited-sound4-growth-001/hardware-acceptance-001.json)
- [Earlier user confirmation](../experiments/edited-sound4-growth-001/manual-observation.json)
- [Original restore registration](../experiments/edited-sound4-growth-001/restore-registration.json)
- Current read-only export: `experiments/exported-generated-sound4-growth-001/project.json`
- Capture SHA-256: `895d593e7a632fbd3154721a2c53b71b0dc69efffa627da8d5a62d9105c263f0`
- Artifact SHA-256: `06c2af8c56fdd52aa05e829f79e3319c712f05ad134e825c69b113c80ee89885`
- Native body SHA-256: `5e6946b26c77ec47d4bea2f02809810754d32369512353abd027a3109b01b401`

The export includes six melodic/three calibrated drum previews and31 verified content
files, preserving all source/raw data. The next [generated shrink test](sound4-generated-shrink-control.md)
checks the inverse allocation transition with a newly synthesized shorter tone.
