# Recorded minimum falsifies the four-bit-only model

The user reported **“done and confirmed the sample sounded lower in first recording
than second.”** In the volume-control context this is recorded as lower relative
loudness at minimum; no pitch stability, numeric display, exact gain or silence is
inferred.

Both captures independently decode at threshold 0.0063 to 815 checksum-valid packets
ending at byte 156758. All sample data, other sounds, auxiliary bytes, other 15 patterns
and global settings remain exact. Tempo/swing stay 100/9. The maximum return equals
the entire independent earlier loud-state body, including every plain packet:
`e34fbe7f6238c230deeacd96139b26e5ca88bb5f300a7831da87a24e32afaef7`.

| Sound 3 raw cell category | Maximum | Actual minimum | Return |
| --- | --- | --- | --- |
| Previously populated steps 1, 2, 5, 9, 13 | `cdff83` | `0df083` | `cdff83` |
| Previously empty steps | `c00f00` | `000000` | `c00f00` |

The low nibbles all become zero as predicted, but the first primary byte's high
`0xc0` bits also clear in all 16 cells. This **falsifies the four-bit-only mask and
minimum-body prediction**. The original report retains failed preservation/prediction
flags; no candidate is moved or report rewritten to turn it into a success.

Predicted four-bit-only minimum body was
`e84321400674817710d81dc3bf8d79b3b9c84b6b02b2d2b490c407c54db1a66b`.
Actual minimum body is
`4a27f9e161ebc2af32c385f0b62eaeac9ad4f431e95a94ec3cb9aaad1debb440`.
Native decoding and unchanged-source checks pass; the failure is the field hypothesis.

A **new post-observation candidate** spans six contiguous bits, bits 6 through 11 of
the little-endian first two primary bytes (mask `0x0fc0`). All other bits remain exact
between the endpoints. Interpreted contiguously, these endpoints read 0 and 63. However,
endpoints alone also fit two flag bits plus a four-bit value, or another ordering of
the six value bits. No six-bit volume semantic or numeric UI range is confirmed yet.

Immutable hardware observations preserve the failed four-bit model, endpoint bytes,
original WAV/artifact hashes and relative user report. Capture peaks are approximately
0.159/0.153 without clipping. The current genuine read-only export is
`experiments/exported-sound3-volume-range-return-maximum-001/project.json`; all 31 content
hashes and complete native-body reconstruction pass. Raw pattern parameters remain
opaque, and sample previews do not render their gain changes.

- [Original failed-model results](../experiments/sound3-volume-lock-range-results-001.json)
- [Minimum hardware observation](../experiments/event-045-c-sound3-tone-volume-lock-minimum/hardware-observation-001.json)
- [Exact maximum-return observation](../experiments/event-046-b-return-sound3-tone-volume-lock-maximum/hardware-observation-001.json)
- [Next interior controls](sound3-volume-middle-series-control.md)

The next series declares both bit orderings and a zero/nonzero-enable alternative
before interior data. Quarter and halfway positions have no exact guessed body or UI
number; mechanical-position bands are auxiliary evidence only. All 13 affected tests
pass, including the real failed minimum and independent alternative models. Public
volume editing remains disabled; production writers are unchanged.
