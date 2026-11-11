# Recorded FILTER A clockwise changes only the candidate bits

The new capture independently decodes at threshold0.0063 to815 checksum-valid packets
and end byte156758. Its complete body is
`95572be728c21f74a220664c26c19982cf0913adf52636ed1d9ef352d2f56f0f`.
Only the preregistered second-primary0xf0 / third-primary0x03 masks change in all16
Sound3/Pattern1 cells. Pitch14, volume36, auxiliary keys, other third-byte bits,
samples, globals, other sounds/patterns and the footer remain exact.

The contiguous projection gives62 in all16 cells; the alternate high-nibble-as-more-
significant grouping gives59. Existing note tuples change`0ef983`→`0ee983`, while
parameter-only tuples change`0e0900`→`0ee903`. The third-high-six raw values remain
32 at existing note cells and0 elsewhere; they are not decoded as resonance by this
pass. Broader location flags include the strict mask and do not imply wider changes.

The user describes high-pass filtering until the sample is no longer audible, with
the bottom display bar initially full around the midpoint and losing segments toward
the right. The exact message is retained separately. This is qualitative inaudibility,
not a measured digital-zero claim, a cutoffHz value or a reported numeric code.
Stored sample bytes and volume remain intact.

A separate post-observation62 rule reproduces the whole actual body. The clockwise
endpoint was not guessed before its data, and this model does not become a retroactive
prediction. Bit order, scalar interpretation, width, mode flags and frequency law
remain unknown;63 in the earlier note cells is retained without calling it bypass.

Backup peaks near0.150/0.144 remain suitable. All31 content hashes and full native
reconstruction pass for the latest genuine read-only export:
`experiments/exported-sound3-filter-A-clockwise-001/project.json`.
Raw previews preserve samples without rendering their pattern filter settings.

- [Immutable native probe](../experiments/sound3-filter-probe-results-001.json)
- [Manual observation](../experiments/event-055-b-sound3-filter-A-lock-up/manual-observation.json)
- [Separate hardware observation](../experiments/event-055-b-sound3-filter-A-lock-up/hardware-observation-001.json)
- [Explicit post-observation model](../experiments/event-055-b-sound3-filter-A-lock-up/clockwise-post-observation-model-001.json)

The next [counterclockwise endpoint and exact return](sound3-filter-A-range-control.md)
keeps the same masks. No filter writer or extension of pitch/volume context is enabled.
