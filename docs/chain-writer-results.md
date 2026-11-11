# Chain writer verified

The [chain writer test](chain-writer-control.md) wrote the chain 5, 1, 1 through
`set_pattern_chain`. The backup equals the compiled target exactly. The person pressed
only play and heard falling, rising, rising, then the cycle again.

All five measured loops match `chain_5_1_1` on all 16 steps within 20 cents. Both
alternatives fail: `first_entry_only` matches 2 loops and `two_entries_alternate` matches
2 loops.

So the device plays a written chain in entry order from the first entry after a restore,
repeats patterns that appear twice, and stops at the stored length. `set_pattern_chain`
is hardware verified.

- [Registration](../experiments/chain-writer-registration-001.json)
- [Decision](../experiments/chain-writer-decision-001.json)
- [Observation](../experiments/compiled-chain-writer-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-chain-writer-001/project.json`

The next [drum pitch test](drum-pitch-control.md) checks the pitch code on drum notes.
