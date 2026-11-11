# Sound 2 removal restored and recaptured exactly

The user reports **"done and confirmed"** after restoring the removal candidate,
saving the requested backup, checking Sound 2 Step 1 off / Step 9 on and the four
Sound 3 lights, and checking playback. Every registered comparison passes.

| Evidence | Result |
| --- | --- |
| Capture | `experiments/edited-sound2-remove-001/capture.wav` |
| WAV SHA-256 | `aa8c083704bb92aa44893bafc3abd35e2bc05182fbb01ca7511f04752dafeb7d` |
| Format | Stereo PCM16, 44.1 kHz, 1,121,904 frames, 25.44 seconds |
| Peak | Left 0.18082, right 0.17395; no near-full-scale samples |
| Decoder | Normal sign-crossings-0.2 at threshold 0.0063 |
| Native body SHA-256 | `1e493f1495ecf2dc68077a35ae97b8883acbe96b94d0798427a9f3f990a1761a` |
| Artifact SHA-256 | `0a79c633e5d383ce066c4ce8ecc4f76275f41543e3744dd6ee6895db9b9b1fed` |
| Packet count / frame end | 511 / 89396 |
| Changes | Only Sound 2 primary bytes 3/4/5 and auxiliary 769 cleared; packets 4/7 |
| Preservation | Sound 2 Step 9, every Sound 3 note, samples, headers, other patterns and unrelated packets identical |

- [Exact hardware comparison](../experiments/edited-sound2-remove-001/hardware-validation.json)
- [Original restore registration](../experiments/edited-sound2-remove-001/restore-registration.json)
- [Historical software report](../experiments/generated-sound2-remove-001/software-validation.json)

The software-only report retains its original hardware-unverified status. Acceptance
is recorded separately. Lights and playback are user reported; no independent acoustic
recording was supplied. Capture was requested before step inspection/playback, with no
deviation reported. This verifies the bounded Sound 2 deletion locally, without assigning
meaning to its opaque primary fields or extending support to other sounds.

The regression compares the genuine complete frame and rejects an undeleted backup and
a checksummed modification that also removes the neighbouring Sound 3 primary cell.
The previous cell-copy validation retains its own preservation checks.

`scripts/validate_sound_cell_removal_recapture.py` produced the comparison and refuses
to overwrite an existing report.

The current state is also exported as a [read-only project](project-export.md), with
sample previews, raw pattern views and exact source preservation. The next physical
control changes only Sound 3's sample start: [start-position control](sound3-start-control.md).

The full suite passes **298 tests in 56.02 seconds**. Ruff lint and formatting checks
pass for all **99 Python files**. Source hashes, raw packet roundtrip, all pattern views,
shared sample previews and output overwrite guards are covered.
