# Fine-tempo endpoints and complete 100 BPM return match the model

The user separately confirmed **60, 240, 100** for the three captures. All three pass
815 native checksums at threshold 0.0063. Each transition changes only byte129
(zero-based) of the second `0x7d5c` payload, directly matching the displayed integer BPM.
Every other global byte, sound parameter, sample, pattern and selector remains exact.

Both endpoint bodies equal their preregistered predictions. The return to 100 BPM
equals the complete independently captured original 100 body and all plain packets.
This supports the direct unsigned-byte interpretation at the observed fine-tempo limits
and the intermediate 100 value, without fitting offsets or altering acquisition.

These remain physical observations. The three-preset writer is unchanged; it still
rejects fine values. A generated arbitrary fine-tempo restore is the next gate. This
series does not claim that every integer was independently captured or restored.

- [Series comparison](../experiments/fine-tempo-range-series-results-001.json)
- [60 BPM observation](../experiments/event-034-b-fine-tempo-60/hardware-observation-001.json)
- [240 BPM observation](../experiments/event-035-c-fine-tempo-240/hardware-observation-001.json)
- [100 BPM return observation](../experiments/event-036-a-return-fine-tempo-100/hardware-observation-001.json)
- Current read-only project: `experiments/exported-fine-tempo-return100-001/project.json`

| State | Capture SHA-256 | Native body SHA-256 |
| --- | --- | --- |
| 60 BPM | `4ece0ed862318c0f2ace0d1e6545db4502af6c18be51c5302af713ebee12638e` | `8146205d12593b62c9b88c8ab9ad13603d10e409d84bef4a89e339ce96865f64` |
| 240 BPM | `1f8de2aafb3281ab6a1db133222669f6082a6131e51094e95b3b25ecf7f621dc` | `681d3d77d3e557e7e345dde3928dc41bb62bc3c80b5f958dfd0857d678c68869` |
| 100 BPM return | `17869856b4650d464eab327fc1b3d1eaf840d367f6511b9c2787d1f1cae017f1` | `d01d2cdd2f9cd85aca19e17ebc7967327aba647926faf91dcb2db0fe42de2633` |

Each accepted artifact is `derived/analysis-001/capture.symbols.npz`; hashes are pinned
in the series result and individual observations. All three read-only exports pass their
31 content hashes and complete-body reconstruction. Peaks remain about 0.163 and 0.156
without clipping.

The next [generated 137 restore](generated-fine-tempo137-control.md) edits the current
returned 100 state to a previously unobserved fine value. Its software model independently
reproduces both genuine endpoint bodies, then changes the same fixed byte to 137.
No public fine-tempo writer is promoted in advance.
