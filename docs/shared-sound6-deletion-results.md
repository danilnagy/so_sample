# Deleting shared Sound6 transfers the full sample to Sound7

The capture passes all core controls with951 valid native checksums using the normal
0.0063 acquisition. Its entire native body matches the preregistered full-transfer
model exactly. Only selectors5/6 change.

Sound6, selector5, is now empty. Sound7, selector6, receives the complete32768-code
buffer under self-owner6, header `00000000c078000006` (start0/end30912/owner6). Every
original code, including all tail codes, is byte-identical to the old Sound6 buffer.
The used window is also exact. Retaining the old owner5 buffer/reference fails as an
alternative. No other sound, pattern or non-Sound6/7 plain packet changes.

The native frame loses one packet and14 encoded-body bytes:951 packets/end190215.
This is ownership transfer on deletion of this shared owner, distinct from freeing
the sample data. It does not expose physical RAM addresses or general deletion policies.

The user reported "done"; completion is recorded, and specific audible checks were
not separately confirmed. The decoded Sound7 preview PCM is identical to the previous
Sound7 window. Native preservation is independently established without inferring an
audible observation from the capture.

- [Preregistered models](../experiments/shared-sound6-deletion-predictions-001.json)
- [Native ownership comparison](../experiments/shared-sound6-deletion-results-001.json)
- [Physical native evidence](../experiments/event-026-b-delete-shared-sound6/native-evidence-001.json)
- [User observation](../experiments/event-026-b-delete-shared-sound6/manual-observation.json)
- Current read-only export: `experiments/exported-shared-sound6-deletion-001/project.json`
- Capture SHA-256: `85944505d73d4a6097800da7220bf34badec35633286e1a2771476b9479c9c7b`
- Artifact SHA-256: `678e5c3cf51029b1278ee7023306d60de584d2dbd7b49b6df5de7e9869167371`
- Native body SHA-256: `15122b45a12cbe4ceab6ad4f5c5f7c5980f41ef772a9ed10ba7350e29edac4f1`

The export has seven melodic/three calibrated drum previews and32 checked content
files, retaining every raw/source record. The next [unshared Sound7 deletion](unshared-sound7-deletion-control.md)
tests removal of the final reference and its serialized backing buffer.
