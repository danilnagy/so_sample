# Physical swing S00, S09 and S18

The user reported **“done, S00, S09, S18”** in the registered capture order.
All three independent recordings decode at threshold 0.0063 to 815 checksum-valid
packets ending at byte 156758. Only second `0x7d5c` payload offset 130 changes:
18→0, 0→9, then 9→18. Serialized tempo stays 137 and all other global, sample,
sound-parameter and pattern bytes remain exact.

| Capture | Display | Stored byte | Complete native-body SHA-256 |
| --- | --- | --- | --- |
| event-038-b-swing-minimum | S00 | 0 | `5f25b5efd909c93b0aa0cdbb31d8aff170ea5edeb9ca6dd48eb2d7778ae696cb` |
| event-039-c-swing-9 | S09 | 9 | `ea13a17f3bb7e131ed8c54d3809bd66eeb298425b4f4d62324d1520ae801942b` |
| event-040-a-return-swing18 | S18 | 18 | `51b9358a087173aa4ebd4e49eda47e698ba34c7dd077237ccb7d353291b6eea8` |

The middle and maximum-return bodies match predictions registered before collection.
Minimum S00 also exactly recovers the independent zero-swing 137 BPM body collected
before the first maximum control. Every control and return hypothesis passes.
Channel peaks are approximately 0.162 and 0.156, with no clipping; the reduced capture
levels remain suitable.

The observed physical display bounds are 0 and 18. This positive range cannot
distinguish signed and unsigned representations outside it, and neither percentages
nor clock timing units are established. Only 0, 9 and 18 have independent physical
display evidence. Intermediate numeric values remain hypotheses until tested.

Immutable manual and hardware observations are saved in each capture folder, separately
from the research checker. Each binds the original WAV, decoded artifact and shared
series report. The current genuine read-only export is
`experiments/exported-swing-range-return18-001/project.json`; all 31 content hashes and
complete native-body reconstruction pass.

- [Registered hypotheses](../experiments/swing-range-series-registration-001.json)
- [Series results](../experiments/swing-range-series-results-001.json)
- [Returned-state hardware observation](../experiments/event-040-a-return-swing18/hardware-observation-001.json)
- [Next offbeat timing test](swing-timing-pair-control.md)

The public swing writer remains disabled. Existing tempo editing retains its guard
against the changed opaque global context. Research prepares a separate, source-bound
straight/swing-6 pair to test generated data and audible timing.
