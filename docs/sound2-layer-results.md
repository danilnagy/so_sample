# Sound 2 added with Sound 3 preserved

Every registered preservation and cell-location check passes. Pattern 1 Step 1
contains Sounds 2 and 3; all existing Sound 3 notes, samples, other patterns and
unrelated packets are unchanged. The normal 0.0063 crossing decoder validates all
511 packets directly.

The primary-equality hypothesis **fails**: Sound 2's primary bytes are **0d2831**,
rather than Sound 3's **0df883**. Its auxiliary byte is **F0**, as predicted for
key 1. The different primary parameters remain opaque. The original failed
prediction and its outcome are retained separately from the passing control checks.

| Evidence | Result |
| --- | --- |
| Capture | `experiments/event-011-b-sound2-layer/capture.wav` |
| WAV SHA-256 | `34b9b78a92d62e76383ee2bd673ae1590793e10b2376ed2dd19974d8c1d16549` |
| Format | Stereo PCM16, 44.1 kHz, 1,120,267 frames, 25.403 seconds |
| Peak | Left 0.16788, right 0.16074; no near-full-scale samples |
| Native body SHA-256 | `e2d6c4a33c045deec30c27449a39182dc6bd0fb80bbe002aba85b0678ce4681d` |
| Artifact SHA-256 | `8e47991a4d0fa96cd56e19f1ed40563b053392509c3b3b455fc8924462fb5798` |
| Changes | Bytes 3/4/5: 00 to 0D/28/31; byte 769: 00 to F0 |
| Changed plain packets | Indices 4 and 7 only |

- [Original predictions](../experiments/sound2-layer-predictions-001.json)
- [Control and hypothesis results](../experiments/sound2-layer-results-001.json)

The user replies "done" to the registered protocol, with no deviation reported.
This is a physical note control, not generated cell-copy acceptance or an
independent acoustic polyphony measurement.

`clone-sound-cell` now provides an experimental bounded copy of the observed
Sound 2 **0d2831/F0** cell, with optional Sound 3 neighbours restricted to their
calibrated parameters. It copies only three primary bytes and one auxiliary byte,
preserves other cells, and rejects occupied Sound 2 targets, unknown source
parameters and unsupported neighbours. The previous `clone-step` and Sound 3 key
writer restrictions remain in place.

The generated candidate adds Sound 2 at Step 9, preserving Sound 3 key 7 there.
Only four bytes in packets 5 and 7 change. Full phase/count waveform roundtrip,
exact target recovery and preservation checks pass. Its separate
[hardware restore test](native-sound-cell-restore-test.md) now passes, including the
entire genuine recapture and user-confirmed light/playback checks. See
[cell-copy results](native-sound-cell-results.md).

The full regression suite passes **269 tests in 49.83 seconds**. Tests preserve
failed hypotheses, check the genuine capture and reject occupied and unknown
cell-copy inputs. The newly registered capture also passes the full capture-inspection
check (11.84 seconds). Ruff lint and formatting checks pass for all 94 Python files
in `src`, `tests` and `scripts`.

Reproduce in a fresh directory:

```powershell
.\.venv\Scripts\python.exe scripts/make_sound_cell_candidate.py experiments/event-011-b-sound2-layer/derived/analysis-001/capture.symbols.npz --out-dir experiments/generated-sound2-cell-002
```
