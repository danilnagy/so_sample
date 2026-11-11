# The device retains an exact nine-page sample buffer

The user confirmed restoration, the familiar Sound6 tone, silent Sound7 and unchanged
Sound4/Sound5/Pattern1 checks. Normal0.0063 acquisition passes968 native checksums,
and the entire recaptured body/packet sequence matches the generated target exactly.

Sound6 retains36864 code bytes: nine4096-code pages, not divisible by8192. Its header
is still `00000000c078000005` (start0/end30912/owner5). The complete original32768 codes
and appended4096 zero codes survive, and the logical window remains byte-identical.
Rounding to40960 and dropping the unused page to32768 both fail as alternatives.
Every non-Sound6 plain packet, pattern and earlier sound remains exact; Sound7 is empty.

This proves acceptance of this odd-page serialized capacity with an independently
held logical endpoint. It does not measure physical allocation units, establish
universal capacity rounding or prove a minimum buffer size. Public copy/deletion
contexts remain limited to their previously validated32768-code layouts.

- [Exact recapture comparison](../experiments/edited-sound6-nine-pages-001/hardware-recapture-results-001.json)
- [Separate hardware acceptance](../experiments/edited-sound6-nine-pages-001/hardware-acceptance-001.json)
- [User observation](../experiments/edited-sound6-nine-pages-001/manual-observation.json)
- [Original registration](../experiments/edited-sound6-nine-pages-001/restore-registration.json)
- Current read-only export: `experiments/exported-sound6-nine-pages-001/project.json`
- Capture SHA-256: `4bd755836feb7ac6f1bcaa806838d398dbf58122a2c2a3882a7909f45409150e`
- Artifact SHA-256: `265a082edcd970fbfd78ceb388ab57d36ecd03bb16f293f8c024961f3e415eba`
- Native body SHA-256: `196444b1b49e0826e9ce7f4b0a4672af4e0a19a7b728a9618408a12e1ee3b3a7`

Seven melodic/three calibrated drum previews and all32 export content hashes pass.
The immutable software report stays `hardware_verified:false`; acceptance records the
manual result and exact recapture separately. The next [one-page WAV import](sound6-one-page-import-control.md)
tests a smaller serialized buffer and a new endpoint derived from actual PCM audio.
