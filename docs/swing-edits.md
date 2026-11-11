# Bounded swing edit plans

The `set_swing` operation changes the numeric swing byte within the physical display
bounds 0 to 18:

```json
{"operation": "set_swing", "value": 6}
```

Use the existing schema-1 edit plan with exact source artifact and native-body hashes.
Compile into a fresh directory through `po33 apply-edits`; project JSON remains a
read-only view. Source and target swing must stay within 0 to 18, and source tempo
must stay within 60 to 240 BPM. Bools, floats, strings and out-of-range values fail.

API functions are `calibrated_swing(frame)` and `set_calibrated_swing(frame, value)`.
Only second `0x7d5c` payload byte 130 changes. Tempo at byte 129, samples, patterns,
sound parameters and all other fields are preserved literally. Equal source/target
swing is a no-op. These are numeric values, with no conversion to percent or clock units.

The recognized two-global-record context now masks **only** calibrated bytes 129 and
130. Both 255-byte records must remain at packet indices 1/2 and every other byte must
match the known opaque-record hashes. Unknown swing values or other settings are
rejected. Tempo editing can preserve a supported swing value; the original preset API
still restricts its source and target BPM to 80/120/140.

Independent physical S00/S09/S18 controls reproduce whole native bodies. The new
generated value 6 restores exactly and independently delays offbeats by approximately
27 ms at 137 BPM while retaining the loop period. This supports the bounded integer
policy; it does not claim hardware verification of every interior integer, all unknown
global contexts, or a timer/percentage interpretation.

Public plans replay both accepted straight and swing-6 WAVs byte-for-byte:

- `experiments/replay-swing0-plan-001/plan.json`
- `experiments/replay-swing6-plan-001/plan.json`

Both plans copy the same opaque Step 13 row to empty Step 2 before setting swing.
Their compiler reports remain hardware-unverified. The software workflow records
complete-body equality, exact accepted WAV replay and immutable-source checks.

All **790** regression tests pass. These include complete independent physical bodies,
both byte-exact accepted WAV replays, tempo/swing composition, rejection of unknown
source fields and invalid target types, stale plan refusal, and literal preservation.

- [Physical range results](swing-range-results.md)
- [Generated swing-6 results](generated-swing6-results.md)
- [Plan workflow](../experiments/swing-public-plan-workflow-validation-001.json)
- [Next composition test](joint-tempo-swing-control.md)
