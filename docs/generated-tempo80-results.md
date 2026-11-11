# Generated tempo editing restores the exact intended state

The user reported **done and confirmed, tempo changed to 80**, confirming receive
acceptance, the displayed value, the unchanged samples and the same Pattern1 phrase
at the slower tempo. The recapture passes all 815 checksums at threshold 0.0063 and
equals both the supplied target and the independently genuine 80 preset capture.

Only payload byte 129 in the second `0x7d5c` packet changes 120 to 80. Every other plain
packet byte, sample record, pattern and selector remains exact. The independent display
reading agrees with the restored byte; neither substitutes for the other. This verifies
writing this preset byte through reconstructed backup audio in the observed context.
The original software report remains `hardware_verified:false`; acceptance is separate.

The public edit-plan operation `{"operation":"set_tempo_preset","bpm":80}` now supports
80, 120 and 140 within the recognized opaque global context. Other global bytes are
checked by fixed record hashes, with only byte 129 masked out. Unknown global layouts,
source fine tempos, arbitrary destinations and bool/non-integer arguments are rejected.
All unrelated packets remain literal; sample/pattern content may vary without being reset.

The hash-bound plan `experiments/replay-tempo80-preset-plan-001/plan.json` compiles into
`experiments/compiled-tempo80-preset-plan-001/restore.wav`, reproducing the accepted
WAV byte-for-byte. Public preset operations also reproduce all three genuine native
preset bodies and the inverse 120 body in software. The replay compiler report remains
software-only; no additional device restore is claimed.

- [Native recapture comparison](../experiments/edited-tempo80-001/hardware-recapture-results-001.json)
- [Separate hardware acceptance](../experiments/edited-tempo80-001/hardware-acceptance-001.json)
- [User confirmation](../experiments/edited-tempo80-001/manual-observation.json)
- Current read-only project: `experiments/exported-generated-tempo80-001/project.json`
- Capture SHA-256: `7512efa7fa484824a6e68a2747bb3d4a4a44f031ca02259728248e47e59465f6`
- Artifact SHA-256: `eb049e30b69ec886029aeb357ba63c300c68e67a67a8d5904aa200ad2fd26f5c`
- Native body SHA-256: `2a1a594b027dcd228f20e2b72961e995b27a3c8378643d74ad03a323ce3c17ce`
- Accepted/replayed WAV SHA-256: `ac450d4f900a16c02325787c4926a3a27a07554278b68ff552cfd670ed8f0832`

All 31 content hashes and the reconstructed complete native body pass. Capture peaks
remain about 0.163 and 0.157 without clipping. The next
[fine tempo 100 control](fine-tempo100-control.md) checks a non-preset value without
broadening the public writer in advance. The full documented 60-to-240 range remains
outside the tested writable scope.
