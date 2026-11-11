# Recorded FILTER interiors support the contiguous branch ordering

All three captures independently decode at threshold 0.0063 to 815 checksum-valid
packets and end byte 156758. The low-pass interior has contiguous raw 16
(alternative grouping 1), the high-pass interior has contiguous 52 (alternative
19), and the center return has 63 under both groupings. Each is uniform across
all 16 Sound 3 / Pattern 1 cells.

Only the registered second-primary high-four and third-primary low-two masks
change. Pitch 14, volume 36, auxiliary values, other third-byte bits, sample data
and every unrelated state bit remain exact. The final return reproduces the
entire independent earlier center body and all packets, not just the field values.

The preregistered contiguous scalar-branch hypothesis passes for both interiors:
16 lies strictly between 1 and 32, and 52 lies strictly between 31 and 62. Both
alternate scalar-branch predictions fail: 1 is outside the registered low-pass
interval 4–32, and 19 is outside the high-pass interval 31–59. These failures
remain in the immutable report. This supports the contiguous grouping's branch
ordering; it does not exclude every possible nonmonotonic interpretation of the
alternative grouping or establish a complete filter law.

The user reports: "done, heard low pass filter applied in first, high pass in
second, no filter in last". These are explicit qualitative listening confirmations
for the requested three captures. No numeric UI reading or new quantitative
audio response is inferred. The user-confirmed center cue remains a single middle
tick. Earlier failed numerical midpoint predictions remain unchanged.

The complete bodies are:

| Capture | Contiguous / alternative | Body SHA-256 |
| --- | --- | --- |
| Low-pass interior | 16 / 1 | `b5e315b3f0703190ad42652eb57616385e52b2c92df04e3aa2bc1b936c005c37` |
| High-pass interior | 52 / 19 | `fd5c085eae8bcea16f167c240d014f770e588c0a205c1117c732021afa0102af` |
| Exact center return | 63 / 63 | `8f80a398ac7130f1802ba865985cb3f7174f9f0129af1182eb6d5da450d6a341` |

Capture peaks stay below 0.146 full scale without clipping; the established reduced
level remains suitable. Current genuine read-only export:
`experiments/exported-sound3-filter-A-interior-center-return-001/project.json`.
All 31 content hashes and complete native reconstruction pass. Raw previews retain
unchanged sample codes and do not render filter effects.

- [Immutable report and both branch outcomes](../experiments/sound3-filter-A-interior-results-001.json)
- [Low-pass hardware observation](../experiments/event-059-f-sound3-filter-A-lowpass-interior/hardware-observation-001.json)
- [High-pass hardware observation](../experiments/event-060-g-sound3-filter-A-highpass-interior/hardware-observation-001.json)
- [Exact-center-return hardware observation](../experiments/event-061-h-return-sound3-filter-A-center/hardware-observation-001.json)
- [Next generated fixed-16/52 restore controls](generated-sound3-filter-pair-control.md)

Both generated WAVs recover these entire independent interior bodies and every
packet in software. Their reception and listening checks remain new hardware
tests. All 88 affected FILTER/pitch checks pass. Production code is unchanged since
the full 917-test run; no public filter writer, all-code cutoff law, UI scale or
resonance field is enabled. Software reports remain hardware-unverified and
physical observations stay separate.
