# Sound 3 start moved; second-field predictions rejected

The user reports **"still hear the tone and done"** after the registered knob A
control. Every preservation check passes: only the Sound 3 nine-byte reference
packet changes, with all backing codes, ownership, other sounds, all sixteen patterns
and unrelated packets preserved. The normal 0.0063 crossing decoder validates all
511 checksums directly.

The reference changes from **00000000401f000000** to **a17a0000ffff000000**:

| Raw field | Before | After |
| --- | ---: | ---: |
| First u32 little-endian, bytes 0..3 | 0 | 31393 |
| Second u32 little-endian, bytes 4..7 | 8000 | 65535 |
| Owner ID, byte 8 | 0 | 0 |

Only offsets 0/1/4/5 within plain packet index 375 change. This supports the first
field's response to the start control. Both registered second-field hypotheses fail:
it stays neither 8000 nor at first+8000 (39393). The observed 65535 is preserved as
a raw value; endpoint, length and special maximum/sentinel interpretations remain
unresolved. The physical knob B was requested untouched, with no deviation reported.
Knob coupling or boundary adjustment may explain the result, but is not established.

The tone remains audible according to the user. Its duration, frequency and exact
physical start were not measured, so this report does not claim unchanged length.

- Capture: `experiments/event-012-b-sound3-start/capture.wav`
- WAV SHA-256: `24502f734e1d9170a1c5a4ac89d104fafeec3514478f39749919521336f68673`
- Stereo PCM16, 44.1 kHz, 1,081,082 frames, 24.514 seconds; peaks 0.16788/0.16064,
  with no near-full-scale samples.
- Native body SHA-256: `4b697a34bea74f34654107463a9586afe31e9db1b55bf11f4f057f6e7f72ddc2`
- Artifact SHA-256: `e569b316e6f67a880206ab17bc6c1839f571fa8b93a985e4b3357f73175d35f7`
- [Original hypotheses](../experiments/sound3-start-predictions-001.json)
- [Separate control and hypothesis evaluation](../experiments/sound3-start-results-001.json)

No nonzero-start writer or extractor is enabled. The new read-only project at
**experiments/exported-start-project-001/project.json** retains all packets and pattern
views exactly. It exports supported zero-start previews for Sounds 1/2/8 and explicitly
marks Sound 3's layout unsupported for preview. The previous four-preview baseline
project remains unchanged. All 25 content-file hashes in the new export are verified.

Regression tests reproduce this genuine capture, retain both failed predictions,
classify the registered alternatives separately using synthetic comparison vectors,
and reject checksummed pattern, backing-code and ownership changes. A separate export
test checks that the unknown nonzero-start record is retained without a fabricated preview.

The full regression suite passes **305 tests in 97.87 seconds**. Ruff lint and formatting
checks pass for all **101 Python files** in `src`, `tests` and `scripts`.

The next control sets only knob B to minimum while leaving start 31393 unchanged.
The independently observed zero-start minimum is 79. A new second field of 79 would
fit the length hypothesis, while 31472 (=31393+79) would fit the endpoint hypothesis.
Other values remain failures of these predictions; inclusive/exclusive endpoints and
the earlier 65535 value would still require care. See [minimum-length control](sound3-start-min-control.md).
