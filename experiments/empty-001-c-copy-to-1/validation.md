# First copied-slot capture validated

Source SHA-256:b38ea70cc43b6ebbb2797a213c156bc396c59eb57648de1c4e9943a4544eaa74.
Original stereo44100 Hz PCM16,1063407 frames,24.113537s including recording margins.
Peak amplitudes0.16818/0.16107 are unclipped. At threshold0.0063 both channels contain
178868 complete phase labels:21 more than the Sound8-only pair. Partial final sign
intervals are left[0,1,0], right[1,1]. These are retained, not padded or trimmed.

The independent amplitude clock has zero complete-label and four-quarter disagreements
in the checked interior. See ../waveform-probes-012.json. This capture is not byte-identical
to a previous recording and has been pinned separately in the fixture manifest.

First strict change versus the Sound8-only state is43270 on both channels. After a
diagnostic shift of-84, source phase increments[76819,177169) exactly match this capture's
[76735,177085), length100350 per channel. The circular phase offset there is0 on both
channels, and the report also records exact raw-label overlap. Multiple unique long
anchors independently locate the same displaced region. No array was normalized or rewritten.

The small growth plus large shared block supports reused transmitted content. It does
not prove physical-memory aliasing, pointer format, compression or native PCM boundaries.
The preceding region still differs densely; the complete stored waveform is not decoded.
No sound/reference field is safe to edit from this result.

The Sound8 addition first changed43354, while this Sound1 copy first changes43270:
difference84=7*12. A12-label sound-slot spacing is a post-observation hypothesis involving
different operations and before-states. It requires an independent destination test.

Next: copy existing Sound8 into empty Sound2, retain Sound1 and Sound8, return to Sound8
with Pattern1 empty/write off/playback stopped, and record one backup in
../empty-001-d-copy-to-2/capture.wav. Predictions are pinned before that capture in
../second-copy-predictions-001.json; both proposed location models may fail.

Three focused tests passed: two independent equality-offset controls and the genuine
copy regression, including source/symbol hashes and exact shared-block boundaries.
Ruff lint/format checks pass; source WAV remains untouched. No hardware-generated
restore or edited state was attempted.
