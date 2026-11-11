# Fixed-start minimum preserved; exact minimum predictions failed

All registered preservation checks pass. Sound 3's first field stays **31393**,
owner stays 0, and only its second field changes from 65535 to **31504**. All sample
codes, other sound records, all sixteen patterns and unrelated packets are identical.
The normal 0.0063 crossing decoder validates all 511 checksums directly.

The resulting reference is **a17a0000107b000000**, differing only in bytes 4/5 of
plain packet index 375. The difference second-first is **111**. Both exact registered
predictions fail: stored length 79 and endpoint 31472 (=31393+79). The new value is
not substituted into either prediction, and 111 is not declared a general minimum.

| Evidence | Result |
| --- | --- |
| Capture | `experiments/event-013-b-sound3-start-min/capture.wav` |
| WAV SHA-256 | `8c13edb2051ecaf7253b491449826ead3f9083a64c6f4b287cdcb3225dc0682b` |
| Format | Stereo PCM16, 44.1 kHz, 1,134,134 frames, 25.717 seconds |
| Peak | Left 0.16800, right 0.16074; no near-full-scale samples |
| Native body SHA-256 | `002346273de5b027d53b593e8183b3695ba680bcd01543286def0bc68d24f696` |
| Artifact SHA-256 | `3b6eb02794d58a4a08094dd53ace16147a03e5f61696adbf72864d2dc2d79b90` |

- [Original predictions](../experiments/sound3-start-min-predictions-001.json)
- [Separate preservation and exact-hypothesis results](../experiments/sound3-start-min-results-001.json)

After the capture, the user independently auditions Sound 3 key 1 with write off,
without moving knobs, and answers **"Very short click or burst"**. That supports a
local endpoint interpretation: 111 codes form a short window, while a literal
31504-code length would retain a substantial tone segment. This is a user-reported
acoustic discriminator, not a recorded duration measurement. See
[audition evidence](../experiments/event-013-b-sound3-start-min/audition-observation.json).
The earlier result report, generated before this observation, is preserved unchanged.

An experimental endpoint writer now accepts only **Sound 3, fixed start 31393,
owner 0 with 65536 backing codes, endpoints in the observed interval 31504..65535**.
It changes only bytes 4..7, retaining all other data. It reproduces the complete genuine
larger-endpoint body and minimum inverse exactly. Other starts, sound slots, unknown
ownership and out-of-range endpoints are rejected. Minimum-width quantization,
inclusive/exclusive endpoints and the special maximum value remain unresolved.

A separate experimental preview reads the selected raw codes using the declared
**half-open [start,end)** convention, without applying keyboard pitch or gain changes.
The default read-only project exporter retains its previous zero-start-only preview
policy; this experimental function does not silently reinterpret older exports.

The next candidate sets endpoint **39393**, retaining start31393 and selecting 8000
codes under the preview convention. Only reference bytes 4/5 change; all samples,
other sounds and patterns remain intact. It passes software waveform and packet
roundtrips and needs its own [hardware restore test](native-nonzero-trim-restore-test.md).

The full suite passes **327 tests in 58.37 seconds**. Ruff lint and formatting checks
pass for all **104 Python files**. The new tests retain failed exact predictions,
reproduce whole genuine endpoint bodies, verify the explicit preview slice and reject
changed starts, ownership, buffer shapes, other sounds and out-of-range endpoints.
