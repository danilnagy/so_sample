# Sound 2 cell copy restored and recaptured exactly

The user reports **"done and confirmed"** after restoring the generated cell copy,
saving the requested backup, inspecting the Sound 2 and Sound 3 step lights and
checking playback. The recapture matches the entire generated native frame exactly.
All 511 checksums validate with the normal 0.0063 crossing decoder; no measured-clock
fallback is required.

| Evidence | Result |
| --- | --- |
| Capture | `experiments/edited-sound2-cell-001/capture.wav` |
| WAV SHA-256 | `1adb6964a06f239adfcd599c2996b6d2d075e67576e63955e150ec8c5d84b56f` |
| Format | Stereo PCM16, 44.1 kHz, 1,095,691 frames, 24.846 seconds |
| Peak | Left 0.17999, right 0.17374; no near-full-scale samples |
| Native body SHA-256 | `4362aa66f6c18e7351b39016eb1b801dfa4a6ce0f4935861d4aaf45c8737668b` |
| Artifact SHA-256 | `cb4c7f9dec20b2d06e95d72aa79cf3aa05dc518619ccfb731386972c44da0e2b` |
| Sound 2 | Identical 0d2831/F0 cells at Steps 1 and 9 |
| Sound 3 | Original keys 1/2/7/16 at Steps 1/5/9/13 |
| Changes from physical addition baseline | Only primary bytes 387/388/389 and auxiliary 897; packets 5 and 7 |
| Preservation | Original Sound 2 cell, all Sound 3 cells, samples, headers, other patterns and unrelated packets identical |

- [Exact hardware comparison](../experiments/edited-sound2-cell-001/hardware-validation.json)
- [Preserved restore registration](../experiments/edited-sound2-cell-001/restore-registration.json)
- [Historical software validation](../experiments/generated-sound2-cell-001/software-validation.json)

The software-only report retains its original `hardware_verified: false`; the new
hardware report records acceptance separately. Light and playback checks are user
reported; no independent acoustic recording was supplied. Capture was requested before
step inspection/playback, and the user reports completion without a deviation.

This validates the bounded Sound 2 cell copy with calibrated Sound 3 neighbours on
this device and playback path. Sound 2's primary parameters remain opaque and differ
from Sound 3's; the earlier equality hypothesis remains rejected. Other sounds and
Sound 2 keys are unsupported.

The next experimental operation removes an observed Sound 2 cell. Inverse checks
reproduce the entire genuine one-cell control and four-key baseline: removing Step 9
undoes the copy, removing Step 1 from the physical control undoes the addition, and
removing both cells from the recapture reproduces the four-key baseline. These are
exact software comparisons, not new hardware deletion tests.

The next candidate removes **Sound 2 at Step 1**, keeps its Step 9 copy and preserves
every Sound 3 cell. Copying the remaining Step 9 cell back to Step 1 exactly recreates
the current complete body in software. See [removal restore test](native-sound-cell-removal-test.md).

The full regression suite passes **288 tests in 51.10 seconds**, including genuine
recapture equality, complete inverse bodies and rejection of valid-checksum changes
to samples or neighbouring notes. The bounded remover rejects empty, partial and
unknown cells; its CLI protects input aliases. Ruff lint and formatting checks pass
for all **96 Python files** in `src`, `tests` and `scripts`.
