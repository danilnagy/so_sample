# Recorded FILTER A endpoints and exact return

Both new backups independently decode at threshold 0.0063 to 815 checksum-valid
packets, ending at byte 156758. The counterclockwise endpoint has contiguous raw
projection 1 (alternate grouping 4) in all 16 Sound 3 / Pattern 1 cells. The
clockwise return has projection 62 (alternate 59), and its entire body and all
packets exactly match the independent earlier clockwise backup.

Only the preregistered second-primary high-four and third-primary low-two bits
change. Pitch 14, volume 36, auxiliary values, other third-byte bits, samples and
all unrelated state remain exact. Existing note tuples become `0e1980` at the
counterclockwise end and return to `0ee983`; parameter-only tuples become
`0e1900` and return to `0ee903`.

The user reports: "done, and confirmed it went from max low pass filter and not
audible to max high pass filter and not audible". This supports the reported
physical endpoint behavior; no numeric display value or measured digital silence
is inferred. Both capture peaks remain below 0.15 full scale without clipping,
so the established reduced recording level remains suitable.

The counterclockwise body is
`32dd3d1db8a515bd284371ac698f0ce21872fccf5a5508f69ad4628818640799`.
The exact clockwise return is
`95572be728c21f74a220664c26c19982cf0913adf52636ed1d9ef352d2f56f0f`.
The literal raw-1 model was written after observing the counterclockwise data;
it is explicitly separate from the preregistered full clockwise return prediction.

The current genuine read-only export is
`experiments/exported-sound3-filter-A-return-clockwise-001/project.json`.
All 31 content hashes and complete native reconstruction pass. Raw sample previews
retain unchanged sample codes and do not render the reported filter effect.

Endpoint results alone do not establish bit grouping, scalar versus mode encoding,
full field width, cutoff frequency law or resonance. Both literal projections
remain available, and the third-byte high-six bits remain opaque. No public filter
writer is enabled; existing pitch and volume guards stay unchanged.

- [Immutable range report](../experiments/sound3-filter-A-range-results-001.json)
- [Counterclockwise hardware observation](../experiments/event-056-c-sound3-filter-A-lock-down/hardware-observation-001.json)
- [Exact-return hardware observation](../experiments/event-057-d-return-sound3-filter-A-lock-up/hardware-observation-001.json)
- [Post-observation raw-1 model](../experiments/sound3-filter-counterclockwise-post-observation-model-001.json)
- [Next center and ordinary-playback control](sound3-filter-A-center-control.md)

Software reports remain hardware-unverified; user and physical capture evidence
is recorded separately. All 53 affected center/range/filter/pitch checks pass.
Production code is unchanged; the last full regression run passed 917 tests.
