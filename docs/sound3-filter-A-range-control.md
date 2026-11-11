# Opposite FILTER A endpoint and exact clockwise return

The clockwise capture has a uniform candidate projection62/alternate59 with pitch14,
volume36 and every other state field preserved. Both next captures are registered
before collection. The counterclockwise endpoint code remains unknown; returning to
the clockwise endpoint predicts the entire independent current body.

Keep Pattern1 / Sound3 / FILTER selected, B and all audio settings unchanged. Use the
same WRITE-held [parameter-lock method](https://teenage.engineering/guides/po-33/en),
section6.

1. **Counterclockwise:** start playback, hold WRITE and slowly turn only A fully
   counterclockwise over5 seconds. Hold WRITE3 more seconds stationary, release WRITE,
   stop playback and ensure write off. Save a complete backup as
   `experiments/event-056-c-sound3-filter-A-lock-down/capture.wav`.
2. Save that first backup before beginning the return. **Clockwise return:** repeat
   the same action with only A fully clockwise over5 seconds. Hold WRITE3 more seconds
   stationary, release WRITE, stop and ensure write off. Save the complete backup as
   `experiments/event-057-d-return-sound3-filter-A-lock-up/capture.wav`.
3. Use the established reduced recording level and one second trailing silence for
   both backups. Do not press keyboard keys or hold BPM/FX during the passes. Report
   the audible/display changes actually observed, including whether the sample
   becomes audible during movement. Leave A at maximum and B untouched after return.

No restore or separate ordinary playback recording is needed. The exact expected
return body is
`95572be728c21f74a220664c26c19982cf0913adf52636ed1d9ef352d2f56f0f`, with contiguous
projection62 and alternate59 in all16 cells. A matching endpoint projection alone is
insufficient if another byte differs.

The strict masks remain second-primary0xf0 and third-primary0x03. Broader third-byte,
primary and auxiliary alternatives remain distinct. Both bit groupings are reported,
without choosing an encoding order, scalar/mode interpretation, cutoffHz scale or
resonance field. Endpoint values and retained ramps are literal; no averages are
used to rescue uniformity. Digital silence and numeric display readings are not assumed.

All50 affected FILTER/pitch checks pass. Tests cover genuine62 evidence, unknown
opposite values, both projections, ramps, unchanged passes, coupled third bits,
hidden return changes, stale hashes and rejection by the existing pitch guard.
Production code is unchanged; the last full regression run passed917 tests.

- [Preregistration](../experiments/sound3-filter-A-range-registration-001.json)
- [Verified clockwise result](sound3-filter-A-clockwise-results.md)
- [Range checker](../scripts/check_sound3_filter_range.py)

After independent decoding of both captures at threshold0.0063:
`python -m scripts.check_sound3_filter_range`.
Software reports remain hardware-unverified; physical and user evidence stay separate.

## Completed

The counterclockwise endpoint has uniform contiguous 1 / alternate 4. The clockwise
return has uniform contiguous 62 / alternate 59 and matches the entire independent
earlier body and all packets. Pitch 14, volume 36 and every noncandidate bit remain
exact. The user confirms low-pass and high-pass endpoints were both inaudible.
See [results](sound3-filter-A-range-results.md) and the
[next center control](sound3-filter-A-center-control.md).
