# Post-restore backup: content comparison remains unresolved

The user reported successful restoration of corrected candidate 002 and supplied this
post-restore backup. The recording is valid 44.1 kHz, signed 16-bit stereo, 253.739932
seconds, with no clipping. SHA-256:
45d3ac95193c239e4cfadbae65e832a040506a81a200ff4472d7084255354c79.
Original and post-restore recordings remain untouched.

The capture is about 0.315 of baseline amplitude. Decoding at threshold 0.02 gives
1,970,366 labels per channel and substantial differences, beginning around index 8730.
A separately documented amplitude-scaled threshold of 0.0063 gives 1,970,367 labels
per channel, matching baseline 002/003 counts, but does not resolve the differences.

At that threshold, left differs in 1,729,979 positions and right in 696,558 positions.
Opening labels match through the first 8,729 positions on both channels. Much of the
later left stream is a constant phase inversion; the later right stream matches.
The earlier differences are not explained by a uniform phase rotation or constant
alignment: 128-symbol anchors at positions 20,000 and 100,000 have no exact match under
any of four phase rotations. Matches found in repeated later regions are not unique
alignment evidence. No alignment has been applied to produce an equality claim.

Reports: comparison-summary.json, derived/validation-001/ (threshold 0.02, full strict
changed ranges), and derived/amplitude-threshold-001/ (threshold 0.0063). The summary
tracks phase labels, not verified protocol bytes or musical fields.

This result does not prove the restored samples or patterns are wrong. State changes
made while checking the device, transport coding or decoding need to be distinguished.
The user has been asked whether samples/patterns match and which controls changed before
this backup. Field editing remains deferred until these differences are understood.

## User clarification

The user reports everything sounded fine, confirms a lower recording level, and says the
pattern sequence may have changed before capture. This strengthens behavioral acceptance
evidence but makes this recording a confounded comparison of device state. A pattern-sequence
change could affect serialized state; it has not been shown to explain the observed symbol
differences. Recording gain alone does not explain them, since the amplitude-scaled threshold
experiment preserved counts without resolving content differences.

Next controlled check: restore the same corrected candidate again, then back it up immediately
without playing, selecting or changing patterns/sounds, or altering settings. Keep the recording
setup and level consistent and preserve the full stereo PCM WAV. Store it separately as
experiments/reconstructed-002/capture.wav. This recording will distinguish unchanged-state
restoration from UI changes made during musical checks.
