# Mixed effects restore and higher-then-lower listening pass

The independent physical capture recovers815 checksum-valid packets ending at
156758 and matches the entire generated target body:
`301798098c33bd2d73186e673239467242f33116507acf5f4beb235e50e0c7b1`.
Pattern1 footer bytes are `6666666677777777`, global131 remains7, and every other
state byte equals the known clear source. The fixed native prediction passes.

The user reports: "done and confirmed I heard first high then low". This supports
the predicted order of the two sections. No instrumented step boundary or numeric
frequency ratio is inferred. Both nibble orders give the same eight6/eight7
projection, so this result cannot decide which nibble belongs to the earlier
step within a pair.

The recording is unclipped, with channel peaks0.15222/0.14749.

- [Frozen prediction](../experiments/pattern1-generated-mixed-FX-halves-global7-registration-001.json)
- [Immutable native result](../experiments/edited-pattern1-FX6-7-halves-global7-001/hardware-recapture-results-001.json)
- [Hardware observation](../experiments/edited-pattern1-FX6-7-halves-global7-001/hardware-observation-001.json)
- [Literal listening report](../experiments/edited-pattern1-FX6-7-halves-global7-001/manual-observation.json)

Current genuine read-only export:
`experiments/exported-pattern1-FX6-7-halves-global7-001/project.json`, with all31
hashes and full native reconstruction verified. Public effect plans remain
uniform-only in their calibrated context. Original reports, predictions and
creation-time writer status remain unchanged.

The next [complementary first-pair control](pattern1-FX-first-pair-control.md)
tests F6 versus6F at the first footer byte with the remaining fourteen effect
nibblesF. Separate first-note audio measurements can distinguish the two local
ordering hypotheses. All100 affected checks pass; production code is unchanged
since the full1,246-test run.
