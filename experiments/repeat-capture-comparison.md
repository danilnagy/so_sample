# Repeated unchanged-capture comparison

All three original recordings were preserved and their SHA-256 hashes verified unchanged.
The new captures are signed 16-bit, 44.1 kHz stereo, with different channels and no detected
full-scale clipping. Capture 002 and 003 each last 253.980544 seconds; capture 001 lasts
256.6 seconds. Recording duration is not transport-content length.

## Acquisition experiment

The upstream-compatible default crossing threshold (10/32768, about 0.000305) lies below
measured lead/tail noise. The maximum absolute sample in the first/last 100 ms of these
captures was 0.002838. Candidate transfer activity independently measured using 10 ms
stereo RMS windows above 0.05 begins around 0.46, 0.86 and 0.69 seconds respectively.
These RMS windows locate signal activity only; they do not establish protocol framing.

A separately recorded experiment uses normalized crossing threshold 0.02, above measured
boundary noise and well below transfer amplitude. This choice was based on signal levels,
not an alignment search. No phase mapping, shift or trimming was applied. The default
artifacts remain stored unchanged. The original WAVs were not filtered or edited.

| Capture | Default left / right symbols | Threshold 0.02 left / right symbols |
| --- | ---: | ---: |
| baseline-001 | 2,004,469 / 2,004,468 | 1,970,366 / 1,970,366 |
| baseline-002 | 1,984,242 / 1,984,237 | 1,970,367 / 1,970,367 |
| baseline-003 | 1,982,063 / 1,982,056 | 1,970,367 / 1,970,367 |

At default threshold, strict comparisons differ over approximately 74.7?74.9% of the
overlapping phase-label positions. These differences are decoder/acquisition artifacts;
they must not be interpreted as musical-state changes.

At threshold 0.02:

- Captures 002 and 003 have identical complete phase-symbol arrays on both channels.
- Capture 001 matches all 1,970,366 symbols in each overlapping channel exactly.
- Captures 002/003 contain one additional terminal symbol per channel: left=3, right=0.
- Capture 001 stores two incomplete terminal sign intervals per channel: left=[1,1],
  right=[0,0]. Captures 002/003 have no incomplete final cycle signs.
- The extra labels match each channel's ending constant carrier run. This supports a
  terminal boundary explanation; a precise final-cycle synthesis policy is still unverified.
- All endpoints and counts are retained. Capture 001 is not declared fully identical.

This is strong evidence of stable repeated transport labels at the explicit threshold,
including independently acquired channel boundaries. It does not prove payload framing,
state-field interpretation or reconstruction acceptance. The threshold remains an explicit
experiment; the CLI default has not silently changed.

## Recorded evidence

[Machine-readable strict comparisons](repeat-capture-comparison.json) include every pair
and channel for both thresholds, lengths, changes, endpoint tails, zero alignment shifts,
and the first 100 changed ranges. Total range counts and truncation indicators are explicit.
Offsets are zero-based, end-exclusive phase-symbol indices, not protocol byte offsets.

Each capture has inspection.json and experiment.json. Default artifacts are under
`derived/session-2-001`; noise-threshold artifacts, exports, per-channel JSON sidecars,
repeat artifacts and deterministic-run logs are under `derived/threshold-002`.
Two independent runs per capture at threshold 0.02 produced byte-identical NPZ files for
that capture. NPZ files across different captures have different source provenance.

Capture 001 already has a user-reported original-file restore acceptance. No restore result
was supplied for captures 002/003, so their hardware statuses remain not_run. Device state,
interface details and processing settings have not been independently documented.

## Validation and next step

63 tests passed, including inspection and independent decoder processes for all three
captures, pinned whole-stream hashes, explicit endpoint checks, and an independent synthetic
boundary-noise regression. Ruff lint and format checks passed. The capture test now verifies
identical 002/003 streams and the exact one-symbol terminal difference in capture 001.

Next is waveform reconstruction using these explicit-threshold artifacts. Start with capture
002 or 003, whose channel lengths agree and whose complete streams match. Preserve the
captured carrier labels instead of adding an assumed preamble, handle the final cycle
explicitly, validate software decode/encode/decode at both supported rates, then provide
a generated restore WAV for manual device testing. Do not interpret pattern fields yet.
