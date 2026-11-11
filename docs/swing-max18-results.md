# Maximum swing S18 matches the adjacent-byte prediction

The user reported **done, S18 was shown for max swing**. All 815 native checksums pass
at threshold 0.0063. Only payload byte 130 (zero-based) in the second `0x7d5c` record
changes 0 to 18, matching the independently reported display's numeric component.
Tempo byte 129 remains 137. Every other global byte, sound parameter, sample, pattern
and selector remains exact.

This supports the preregistered location and a first positive display association.
It does not establish the minimum, signedness, percentage or timing units, or a swing
writer. The checker deliberately leaves numerical encoding confirmation false after
one point. Tempo display confirmation was not separately supplied; the known tempo
field in the capture is preserved at 137.

- [Native comparison](../experiments/event-037-b-swing-maximum/native-swing-results-001.json)
- [Independent S18 report](../experiments/event-037-b-swing-maximum/manual-observation.json)
- [Hardware association](../experiments/event-037-b-swing-maximum/hardware-observation-001.json)
- Current read-only project: `experiments/exported-swing-max18-001/project.json`
- Capture SHA-256: `2fd1195678408838c33a89488f0a9b131c143c9a962f3a9964d22ef70d290339`
- Artifact SHA-256: `550c905ac802602e69b691b970536c0bc5bfe76cbd4252b1713b516fdcb360f4`
- Native body SHA-256: `51b9358a087173aa4ebd4e49eda47e698ba34c7dd077237ccb7d353291b6eea8`

All 31 export content hashes and complete-body reconstruction pass. Peaks remain about
0.162 and 0.156 without clipping. The next
[minimum/middle/return series](swing-range-series-control.md) observes the unknown minimum,
requests displayed 9 and returns to S18. Public tempo editing still rejects this new
opaque swing context rather than resetting it. No production writer scope is expanded.
