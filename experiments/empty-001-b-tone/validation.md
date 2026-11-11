# One-tone pair validated

The two new original stereo44100 Hz PCM16 WAVs have distinct hashes:

- Sound8-only:74d6be2ea498c4fcebed2963ef127b6a6addee07a87423148b7dae40f1d5c80c.
- Consecutive repeat:284166f13a6e926d1fcf44cb213e82b0c52be6afaf331279836f8716d8cf9a23.

At threshold0.0063 both have178847 complete phase labels per channel, with zero changes
and no shifted/padded endpoints. Both retain the same partial final intervals:
left[0,1,0], right[0]. The original capture durations are23.830227s and24.136576s,
including different leading/trailing recording spans. Peaks~0.168/0.161 are unclipped.
Levels are higher than the empty pair; exact master-volume/recording changes were not
reported. This does not alter the observed matching phase streams or independent checks.

Relative to empty-001-a, both channels preserve every label before43354, then diverge.
The count increase is133814 labels per channel. Shared-span changes are1274 left and
1277 right. These are transport positions/counts, not sample fields or decoded bytes.
Actual recorded sound duration is unknown; button timing can include input silence.

Independent amplitude-derived clock checks have zero label/quarter disagreements in
both tested interiors. Reports: ../waveform-probes-010.json and011.json. Repeat comparison
is ../empty-tone-repeat-001.json; original source/symbol hashes and residual boundaries
are pinned in the capture fixture manifest.

../one-tone-structure-001.json scans the added/altered body in raw, staggered-phase and
phase-increment views. No long520 repetition or strong repeating-tone signature appears
in the chosen windows. Old suffix anchors after43400 are absent in the new increment
stream. A small equal terminal suffix is constant and matches under multiple shifts,
so it is not treated as evidence for a single insertion alignment or a decoded footer.
The previous populated-state520 observation is not promoted to calibration-tone content.

The new genuine-capture test passes, checking both source hashes, label hashes/counts,
residual intervals and the unchanged empty-state prefix. Ruff lint/format checks pass.
No original WAV or prior experiment was edited. No payload codec, native sample rate,
checksum or writable sample field is identified.

Next control: copy existing Sound8 into empty melodic Sound1 using the device's copy
operation, retain Sound8, then return to Sound8 and record one full backup in
../empty-001-c-copy-to-1/capture.wav. That folder has exact button instructions and
explicitly reuses this verified before-state pair. No new analogue sampling is requested.
