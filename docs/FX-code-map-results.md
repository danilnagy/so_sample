# Effect code map: code = FX key - 1

The [device-side code map](FX-code-map-control.md) supports the registered model. Each
of the fifteen patterns holds exactly one code, written uniformly on all 16 steps:

| FX key | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | none |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Footer code | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | A | B | C | D | E | F |

Both controls match: key 7 stores 6 and key 8 stores 7, as in earlier results. With the
confirmed layout, a pattern's effects are fully described by 16 nibbles, step 1 in the
high nibble of footer byte 0. See the [result](../experiments/FX-code-map-result-001.json)
and [observation](../experiments/observe-FX-code-map-001/hardware-observation-001.json).
Current genuine export: `experiments/exported-FX-code-map-001/project.json`.

The same backup changed 17 bytes in the second global record (tag 0x7d5c), outside any
pattern footer. Byte 0 went from 0 to 15, matching the last selected pattern, 16,
counted from zero. Bytes 131 to 146 changed to values from 4 to 15, one byte per
pattern. Byte 131, previously called the opaque global byte, would then belong to
pattern 1. A plausible role is the step where each pattern's playback last stopped.
This is an untested hypothesis. The editor should keep these bytes unchanged.

Only stored codes were mapped. What each effect sounds like was not measured, apart from
code 6, which rises over its step. No per-step effect writer is enabled yet.
