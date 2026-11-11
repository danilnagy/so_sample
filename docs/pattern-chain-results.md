# How the PO-33 stores a pattern chain

The [chain observation](pattern-chain-control.md) restored a known state, then the person
chained patterns on the device. They chained Pattern 1 then Pattern 2 instead of the
registered Pattern 1 then Pattern 5; Pattern 2 is empty. The result is recorded with that
deviation.

Only three bytes changed, all in the second global record. The registered
`chain_in_global_record_only` hypothesis holds.

| Byte | Before | After | Reading |
| --- | --- | --- | --- |
| 0 | 4 | 0 | first entry: Pattern 1, counted from zero |
| 1 | 0 | 1 | second entry: Pattern 2 |
| 128 | 1 | 2 | chain length |

Playback matched Pattern 1 on loops 1, 3 and 5, and loops 2 and 4 were silent, as the
empty Pattern 2 predicts.

So bytes 0 to 127 hold up to 128 chain entries and byte 128 holds the chain length. The
"selected pattern" byte is the first entry of a chain of one. Other backups hold stale
values past the chain length, so only the length decides what plays. The new
`set_pattern_chain` operation writes entries and length. `set_selected_pattern` now writes a
chain of one.

- [Registration](../experiments/pattern-chain-registration-001.json)
- [Result](../experiments/pattern-chain-result-001.json)
- [Observation](../experiments/observe-pattern-chain-001/hardware-observation-001.json)
- Export: `experiments/exported-pattern-chain-001/project.json`

The [chain writer test](chain-writer-control.md) writes a chain in software.
