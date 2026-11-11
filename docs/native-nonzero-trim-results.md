# Fixed-start endpoint edit restored and recaptured exactly

The user reports **"done, and both checks passed"**: Sound 3 key 1 plays a clearly
audible brief tone and Sound 8 key 1 retains its longer tone. The supplied recapture
matches the entire generated target, with all 511 checksums valid and all samples,
other sound records and sixteen patterns preserved.

| Evidence | Result |
| --- | --- |
| Capture | `experiments/edited-nonzero-trim-001/capture.wav` |
| WAV SHA-256 | `7935f7cfe3ab7a8b8d45dbe942f3144dad2c7eebb09c8aa52fb06f96a1d632d8` |
| Format | Stereo PCM16, 44.1 kHz, 1,087,947 frames, 24.67 seconds |
| Peak | Left 0.17679, right 0.16998; no near-full-scale samples |
| Decoder | Normal sign-crossings-0.2, threshold 0.0063 |
| Native body SHA-256 | `b3296f2ed7b3a74cedc79b8d89900e5128c7da1da0e2fed9839d1858412eddfe` |
| Artifact SHA-256 | `903488a982528ae6b2eb05e2ff48c50ad39d810f611c8e65a8c94481033ec558` |
| Sound 3 | Start31393, endpoint39393, owner0; raw header a17a0000e199000000 |
| Changes from minimum baseline | Only reference bytes4/5 in packet375 |

- [Exact hardware comparison](../experiments/edited-nonzero-trim-001/hardware-validation.json)
- [Preserved original registration](../experiments/edited-nonzero-trim-001/restore-registration.json)
- [Historical software report](../experiments/generated-nonzero-trim-001/software-validation.json)

The software report retains its original hardware-unverified flag; the new result is
recorded separately. Musical checks are user reported, with no independently recorded
duration/frequency measurement. Capture was requested before audition, with no deviation
reported. The fixed-start endpoint edit is now locally hardware validated. Other starts,
general minimum quantization, endpoint inclusivity and the maximum marker remain unresolved.

Project export can now explicitly include this calibrated Sound 3 preview with
`--calibrated-windows`. The actual verified state is exported at
**experiments/exported-verified-window-001/project.json**. All 26 content-file hashes
are checked. The preview uses declared half-open[start,end) selection and nominal-rate
resampling, retaining raw codes and provenance. Default export behavior remains unchanged.

The new [JSON edit-plan workflow](edit-plans.md) uses existing bounded writers and source
hashes. Its replay produces a restore WAV **byte-identical** to the file just accepted
on hardware. That proves this replay without a new device operation. The compiler's
software-only report remains separate from its matching hardware evidence.

The next [quarter-position start control](sound3-start-quarter-control.md) checks a second
start value before extending the fixed-start writer.

The full suite passes **338 tests in 58.65 seconds**. Ruff lint and formatting checks
pass for all **107 Python files**. Tests cover the actual recapture, valid-checksum wrong
endpoints, opt-in preview policy, stale/unsupported plans, ordered edit composition,
source preservation and byte-exact replay of the accepted WAV.
