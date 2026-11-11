# Shared deletion preserves the imported sample exactly

The user confirmed Sound6 is silent, Sound7 retains the same rising sweep, and Sound4,
Sound5 and Pattern1 are unchanged. The physical deletion capture passes all 951 native
packet checksums at threshold 0.0063 and exactly matches the preregistered full-transfer
body. Only selectors5 and6 change.

Sound6's record is empty. Sound7 now owns all 32,768 original backing codes under
header `00000000ab44000006` (start 0 / endpoint 17,579 / owner6), including the entire
15,189-code zero tail. Its logical window is identical to the previous reference's
window. All other sample records, patterns and opaque packets remain exact. Retained
owner5 and dangling-reference alternatives fail.

The public `delete_melodic_sound` operation for Sound6 now supports this imported
endpoint alongside the earlier 30,912 endpoint. It still requires the exact matching
Sound7 reference, a 32,768-code zero-start owner, known packet geometry, no additional
referrers and no Sound6/Sound7 pattern events. Sound7 last-owner deletion retains its
earlier endpoint guard pending a separate physical control.

The hash-bound plan `experiments/replay-imported-shared-sound6-deletion-001/plan.json`
compiles into `experiments/compiled-imported-shared-sound6-deletion-001/restore.wav`.
Its complete native body equals this genuine physical capture. The compiler report
remains software-only; this compiled WAV has not undergone another device restore.
A composed copy/shared-deletion plan independently reproduces the same genuine body.

- [Native recapture comparison](../experiments/event-028-b-delete-imported-shared-sound6/hardware-recapture-results-001.json)
- [Separate hardware acceptance](../experiments/event-028-b-delete-imported-shared-sound6/hardware-acceptance-001.json)
- [User observation](../experiments/event-028-b-delete-imported-shared-sound6/manual-observation.json)
- Current read-only project: `experiments/exported-imported-shared-sound6-deletion-001/project.json`
- Capture SHA-256: `69f7911f772ea76e3ff8a9b8d7ee45e819aaea239ebea982a92484208fd0a429`
- Artifact SHA-256: `11e0decd4bfe263dc674498d94345f42e3c229f5013e4d42aaa4a6fc48d4a0cd`
- Native body SHA-256: `684437bc68251bb2cf3400e64be024d677baeb0e5389106c0122ea30b30724f1`

All 32 exported content hashes and the reconstructed complete native body pass.
Capture peaks are about 0.165 and 0.158, without clipping. The next
[last-owner control](imported-unshared-sound7-deletion-control.md) tests removal of
Sound7 against the independently verified earlier state with both slots empty.
