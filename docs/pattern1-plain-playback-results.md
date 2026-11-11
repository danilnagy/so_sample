# Battery replacement, stopped repeat and plain playback

The user reports: "the batteries died so I installed new ones. recorded the two
captures as described". This is a reported power intervention before the pair,
not an instrumented power-cycle test. No new listening or display confirmation
was supplied.

Both WAVs are distinct from one another and the original clear WAV. Each decodes
at threshold0.0063 into815 checksum-valid packets ending at156758. Both complete
native bodies and every packet equal the accepted clear state:
`3d3762e28817a2bccf83986539c889d1e74e70139b2313affcc3d56cc1bb370b`.

| Capture | Global131 | Pattern1 footer | Change against pre-battery-change state |
| --- | --- | --- | --- |
| Stopped repeat | 7 | FF eight bytes | None |
| After about five seconds ordinary playback | 7 | FF eight bytes | None |

The registered complete-body repeat prediction passes. Both low-four and broader
whole-byte preservation scopes pass, with no global change at all. This stop did
not distinguish the byte's role. A single unchanged playback result does not rule
out every transient role; nor does preserved serialized state establish a general
battery-change guarantee. We do not call global131 a step counter or effect code.

The stopped capture channel peaks are0.15903/0.15314; the playback capture peaks
are0.15833/0.15240. Neither clips. The levels remain suitable.

- [Frozen predictions](../experiments/pattern1-playback-global-registration-001.json)
- [Immutable software result](../experiments/pattern1-playback-global-results-001.json)
- [Stopped-repeat hardware observation](../experiments/event-069-a-pattern1-stopped-repeat/hardware-observation-001.json)
- [Playback hardware observation](../experiments/event-070-b-pattern1-plain-playback/hardware-observation-001.json)

Current genuine read-only export:
`experiments/exported-pattern1-plain-playback-001/project.json`. All31 content
hashes and complete native reconstruction pass. Software results remain
hardware-unverified; separate observations bind the user report, capture and
native evidence. Every earlier result and registration remains unchanged.

The next [generated octave-up test](generated-pattern1-FX-up-control.md) changes
only the footer, keeping global131 at7. It tests whether the earlier observed
octave-up footer works without the co-occurring global9 value. No public writer
or nibble order is inferred. All58 affected tests pass; production code remains
unchanged since the full1,137-test run.
