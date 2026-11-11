# Three tempo presets and exact original return match the byte model

The user independently confirmed **140 to 80, then 80 to 120**. Both captures pass
all 815 native checksums at the established threshold 0.0063. Each transition changes
only payload byte129 (zero-based) in the second `0x7d5c` packet, with the byte equal to
the displayed integer BPM. Every sample, pattern, selector and unrelated plain byte
remains exact.

The 80 BPM body exactly matches its preregistered prediction. The return to 120 BPM
equals the entire independent original backup, including all plain packets and opaque
settings. Together with the first 120-to-140 control, this supports the fixed byte
mapping at all three observed presets and an exact return, without changing the
candidate offset, fitting an encoding or repairing decoder symbols.

These are physical field observations. They do not yet verify a generated tempo
restore or an arbitrary BPM range. Separate hardware-observation reports retain
`writable_field_verified:false` and `tempo_writer_enabled:false`.

- [Series comparison](../experiments/tempo-preset-series-results-001.json)
- [80 BPM observation](../experiments/event-031-b-tempo-80/hardware-observation-001.json)
- [120 BPM return observation](../experiments/event-032-a-return-tempo-120/hardware-observation-001.json)
- Current read-only project: `experiments/exported-tempo-return120-001/project.json`

| State | Capture SHA-256 | Native body SHA-256 |
| --- | --- | --- |
| 80 BPM | `b83a3a086a6c5eef5c365d98b1032d08fe67d29b65afb200f490b27b170cbfcd` | `2a1a594b027dcd228f20e2b72961e995b27a3c8378643d74ad03a323ce3c17ce` |
| 120 BPM return | `80023150ef49d531f72b8b62aad151831a9353b328016751d2388e99fb22e890` | `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0` |

The accepted artifacts are each `derived/analysis-001/capture.symbols.npz`:
80 BPM SHA-256 `7f1b3ac76297a7e7f5fa7a12c392e21438f09532f7ffd939500b0d8e47e4df69`;
return SHA-256 `4c908075fba35546a88bbc01ec352616759419eaeff8da9b6d829cf05903a98f`.
Both read-only exports pass all 31 content hashes and complete-body reconstruction.
Capture peaks remain about 0.164 and 0.157 without clipping.

The next [generated 80 BPM restore](generated-tempo80-control.md) changes the current
120 BPM backup at this fixed byte. Its target already equals the independently genuine
80 BPM native body; the generated waveform still needs device acceptance and recapture.
