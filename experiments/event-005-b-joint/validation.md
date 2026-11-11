# Corrected joint-state capture

The corrected upload is a new stereo 44100 Hz PCM16 recording with source SHA-256
8ae9bae0ec743a18c0de55b482f8c7aecc9125f15c52b0c88a8b765a3cd78d2d.
Peaks are 0.168427 left and 0.160889 right, with no clipping. The validated reduced
recording level remains suitable. Decoding at 0.0063 preserves 1970367 labels on each
channel. Corrected derived data is in derived/analysis-002; inspection-corrected.json
is authoritative for this upload.

The original mistaken upload was exactly event-004-b-repeat. The user confirmed it was
the wrong file and replaced it. Its earlier inspection/analysis-001 and joint-results-001
are retained as ineligible history, not a two-kick experiment. The initial waveform remains
available in event-004-b-repeat; no source waveform was edited by the research tools.

All twelve preregistered predictions fail in their shared span. Corrected comparison is
../joint-results-002.json; original prediction hashes and source hashes matched before
comparison. Unequal prediction endpoints remain explicit and do not explain these failures.
This rejects the fixed XOR/modulo-four models in the three chosen views, under the planned
independent-edit assumption. It does not prove encryption or exclude all possible coding,
especially when UI state, derived metadata or interactions can make state edits non-affine.

The independent amplitude clock agrees with all four quarter signs throughout the checked
interior. See ../waveform-probes-006.json. No additional component data lane is exposed.

Two-kick state versus empty retains a constant relative phase after cell 938283:
offset 0 left and 1 right. Its phase increments versus Step 3-only differ last at index
60010, then match exactly throughout their shared suffix. Relative phase after cell 60011
is 1 left and 2 right. No normalization was applied to stored artifacts. Full pairwise
and baseline summaries are ../framing-probes-003.json and ../staggered-probes-002.json.

A post-observation exact increment-anchor search found one unique source anchor that
reappears at a different joint-state position on both channels. It extends to 1049/1048
binary coordinates on left/right; other sample-region hits had duplicate source anchors
and do not establish unique relocation. See ../increment-anchors-001.json and
../../docs/joint-investigation.md for scopes and limits. No pattern field is writable.
