# Interior volume masks hold; the middle retains a ramp

The user reported **“done, the first is the lowest, second is in between, then the last
one is the highest and loudest.”** This supplies relative loudness order, without
numeric UI readings, exact gain or pitch-stability measurements.

All three independent captures decode at threshold 0.0063 to 815 checksum-valid
packets ending at byte 156758. Only the two candidate Sound 3 masks change. All other
primary bits, auxiliary cells, sounds, sample codes, other 15 patterns and global
settings remain exact. Tempo/swing stay 100/9, and the full maximum return exactly
recovers `e34fbe7f6238c230deeacd96139b26e5ca88bb5f300a7831da87a24e32afaef7`.

| Position | Contiguous six-bit interpretation | Alternate ordering |
| --- | --- | --- |
| Independent minimum | Uniform 0 | Uniform 0 |
| Quarter | Uniform 21 | Uniform 21 |
| Middle | 37, 41, 44, 47 and 46 retained by step | 25, 26, 11, 59 and 43 retained by step |
| Maximum return | Uniform 63 | Uniform 63 |

Middle values in step order under the contiguous interpretation are
`37,41,44,47,47,47,47,46,46,46,46,46,46,46,46,46`.
The middle **does not satisfy the registered uniformity or position-band condition**.
Both complete model-support flags remain false in the original report. This is a
valid saved ramp, not a decoder failure; the data is not replaced by a fitted average
or turned into a passing uniform-middle result.

First-byte pairs `01` and `10` occur, and nonzero values do not always have `0xc0`.
That rejects the separately registered simple zero/nonzero-enable alternative. The
quarter is uniform 21 under both value orderings, making it a useful neutral reference.

A separate **post-observation diagnostic** notes that all contiguous middle values
exceed quarter21, while one alternate-order value does not. This is not retrospective
preregistered evidence: snapshot step order need not be acquisition order, and the
affected low alternate value is at a formerly empty cell. No gain law or definitive
bit order is claimed from that diagnostic alone.

Immutable manual/hardware observations bind WAVs, artifacts, report flags and relative
user confirmation. Capture peaks are approximately 0.164/0.159 without clipping. The
current genuine read-only export is
`experiments/exported-sound3-volume-middle-return-maximum-001/project.json`, with all
31 content hashes and complete body reconstruction verified. Public volume editing
remains disabled.

- [Original model results](../experiments/sound3-volume-middle-series-results-001.json)
- [Post-observation diagnostic](../experiments/sound3-volume-middle-series-post-observation-001.json)
- [Uniform quarter hardware observation](../experiments/event-047-d-sound3-volume-lock-quarter/hardware-observation-001.json)
- [Nonuniform middle hardware observation](../experiments/event-048-e-sound3-volume-lock-middle/hardware-observation-001.json)
- [Next generated gain-ordering test](generated-sound3-volume18-control.md)

The next pair replays the independent uniform21 reference and constructs a fixed new
six-bit value18. The alternative ordering reads the same new bits as36. Those models
therefore predict opposite amplitude directions relative to21. Software waveforms and
all15 affected tests pass; physical reception and ordinary playback remain pending.
Production writers are unchanged.
