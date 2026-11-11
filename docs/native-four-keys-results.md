# Four calibrated keys restored and recaptured exactly

The user reports **"done and confirmed matched"** after restoring the four-key phrase,
saving the requested backup and comparing Pattern 1 to manually auditioned Sound 3
keys **1, 2, 7, 16**. The complete recovered native frame equals the generated target,
with every packet and checksum verified. This completes local hardware validation of
the four calibrated values; it does not establish the untested keyboard values.

| Evidence | Result |
| --- | --- |
| Genuine recording | `experiments/edited-four-keys-001/capture.wav` |
| WAV SHA-256 | `2cc8b8df219f49e9a0721d67ecf719c37575f9f9da7f264eac5b2c4736eb84bf` |
| Format | Stereo PCM16, 44.1 kHz, 1,096,325 frames, 24.86 seconds |
| Peak | Left 0.19733, right 0.18698; no near-full-scale samples |
| Native body SHA-256 | `9b87309f572b188cd1e1a2651b1ca4feec5cfa8fb669068631042ca8f49465f0` |
| Packet count / frame end | 511 / 89396 |
| Pattern 1 | Sound 3 keys 1/2/7/16 at Steps 1/5/9/13 |
| Differences from physical key 7 baseline | Auxiliary 834 F6 to F1, 898 F0 to F6, 962 F1 to FF; only packet index 7 changes |
| Preservation | Samples and headers, all primary note fields, auxiliary upper nibbles, other patterns and every unrelated packet identical |

The original crossing decoder at threshold 0.0063 fails the checksum at wire byte
9941, tag C498. The original WAV, failed artifact and failure report remain unchanged
in `derived/analysis-001` and `initial-decode-failure.json`. The independent
`amplitude-clock-0.1` decoder creates a separate artifact in `derived/analysis-002`.
It uses waveform quarter signs and a unique pre-frame alignment, checks all interior
quarter relations and all native checksums, and reproduces the body exactly.
Neither the generated target nor its expected note values guide recovery.

The recovered artifact SHA-256 is
`853f5ea6670d5b4508190f79d5547453ea9119fa95c98dc06cd02f1e5861d0b0`.
Its explicit windowed waveform coverage remains unsuitable for direct encoding;
verified packet rebuilding is still required to create a new transfer.

- [Hardware comparison](../experiments/edited-four-keys-001/hardware-validation.json)
- [Preserved restore registration](../experiments/edited-four-keys-001/restore-registration.json)
- [Initial crossing failure](../experiments/edited-four-keys-001/initial-decode-failure.json)
- [Original software validation](../experiments/generated-four-keys-001/software-validation.json)

The original software report retains `hardware_verified: false` as historical evidence.
The separate hardware report records the new result. Capture timing was requested before
audition/playback; the user reports protocol completion without a deviation. Musical
behavior is user reported; acoustic frequencies and intervals were not measured.

`scripts/validate_four_key_recapture.py` checks source identity, the registered restore
WAV hash, exact whole-frame equality, all expected byte changes and preservation of
other state. Its regressions independently recover this real WAV and reject an original
backup, a checksummed wrong-key change and a checksummed sample change.

The full regression suite passes **248 tests in 52.57 seconds**. Ruff lint and
formatting checks pass for all **91 Python files** in `src`, `tests` and `scripts`.

The next control adds **Sound 2, key 1 on Pattern 1, Step 1**, retaining its existing
Sound 3 note. This tests another sound cell and two sounds on one step with one new
recording. See [Sound 2 addition](sound2-layer-control.md).
