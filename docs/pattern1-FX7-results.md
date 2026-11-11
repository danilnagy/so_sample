# Recorded octave-up stores footer6 and one global-byte change

Independent threshold0.0063 decoding recovers815 checksum-valid packets and end
byte156758. Pattern1's eight-byte footer becomes `6666666666666666`, giving raw6
in all16 nibbles under both packing projections. Primary/auxiliary data and all15
other patterns remain exact. One other payload byte changes: packet index2, the
second0x7d5c packet, payload offset131 changes0 to9. Every remaining payload byte,
including sample data, pitch14/volume36/cutoff16/resonance32 and keys, stays exact.

The original footer-only hypothesis **fails**, because its nonpattern preservation
check is false. This failed report is immutable. A separate post-observation model
sets the eight footer bytes to0x66 and global byte131 to9, reproducing the entire
native body and every packet. It is explicitly not a prior two-field prediction.
The global byte's meaning is unknown; it is not labeled an effect selector, cursor,
volume field or enable flag. Uniform data does not resolve nibble order.

The user reports: "done, confirmed i heard an octave higher". This explicitly
confirms the audible effect associated with the requested FX7 pass. No measured
2:1 frequency ratio or numeric display is inferred. The full body is
`99b832a7e42f801c9d266da0e4f24d3f4a0add2f2352e24274cf77d7295a276d`.
Backup peaks are approximately0.1320/0.1294 full scale without clipping; established
recording levels remain suitable.

Current genuine read-only export:
`experiments/exported-pattern1-FX7-recorded-001/project.json`; all31 content hashes
and full native reconstruction pass. Raw previews do not render saved effects.

- [Original immutable report and strict failure](../experiments/event-065-a-pattern1-FX7-recorded/FX-probe-results-001.json)
- [Separate hardware observation](../experiments/event-065-a-pattern1-FX7-recorded/hardware-observation-001.json)
- [Exact listening report](../experiments/event-065-a-pattern1-FX7-recorded/manual-observation.json)
- [Explicit post-observation two-field model](../experiments/pattern1-FX7-footer-global-post-observation-model-001.json)
- [Next octave-down and clear controls](pattern1-FX8-clear-control.md)

The next registration tests footer plus low-four or whole global-byte alternatives,
without guessing new global values or rewriting the failed original model. All56
affected checks pass; production code is unchanged since the full1,137-test run.
No public FX writer, full effect map or global-byte interpretation is enabled.
Software reports remain hardware-unverified and physical evidence stays separate.
