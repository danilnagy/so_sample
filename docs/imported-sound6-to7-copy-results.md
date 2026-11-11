# Imported sample copy matches the hardware recapture

The user confirmed the restore and audition checks: Sound6 and Sound7 play matching
rising sweeps, and Sound4, Sound5 and Pattern1 are unchanged. All 952 native checksums
pass at the established acquisition threshold 0.0063. The complete recapture matches
the registered target body and plain packets exactly.

Sound7 retains the nine-byte reference `00000000ab44000005`: start 0, endpoint 17,579,
owner5. Sound6 retains all 32,768 backing codes without duplication, truncation or
metadata changes. Only Sound6 and Sound7 refer to owner5. All patterns and non-Sound7
packets remain exact.

The public `copy_melodic_reference` edit-plan operation now accepts this newly verified
endpoint as well as the earlier 30,912 endpoint. Both require the existing unshared,
zero-start, self-owned 32,768-code Sound6 layout and empty Sound7; other endpoints,
capacities, slot pairs and malformed/shared/dangling-reference contexts remain rejected.
This is a bounded extension supported by the genuine recapture.

The plan `experiments/replay-imported-sound6-to7-copy-001/plan.json`, compiled into
`experiments/compiled-imported-sound6-to7-copy-001/restore.wav`, reproduces the accepted
WAV byte-for-byte. Its compiler report remains `hardware_verified:false`; this replay
does not constitute an additional hardware restore.

- [Native recapture checks](../experiments/edited-imported-sound6-to7-copy-001/hardware-recapture-results-001.json)
- [Separate hardware acceptance](../experiments/edited-imported-sound6-to7-copy-001/hardware-acceptance-001.json)
- [User observation](../experiments/edited-imported-sound6-to7-copy-001/manual-observation.json)
- Current read-only project: `experiments/exported-imported-sound6-to7-copy-001/project.json`
- Capture SHA-256: `36b929195ee52efe831f26edec64ac707800abfb26832c012bfdd1ba5e0f90e1`
- Artifact SHA-256: `12579bb9d19941597d6213f0dba62b4d60e1225e6aa089bfc5241204689bcde7`
- Body SHA-256: `0e9ea03263ec6060838e557ccfc568a90eb3cfc65c2dca7180095736abf72920`
- Accepted/replayed WAV SHA-256: `50d7a759036a91cfd00466ec8d6a77cfb5b3fa959867c140b663b3877dd93af9`

All 33 exported content hashes pass, and exported Sound6/Sound7 preview WAVs are
identical. Capture peaks are approximately 0.165 and 0.159, without clipping. The next
[physical deletion control](imported-shared-sound6-deletion-control.md) checks ownership
transfer at this imported endpoint; public deletion guards retain their earlier scope.
