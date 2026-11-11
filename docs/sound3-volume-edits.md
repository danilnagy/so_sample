# Bounded uniform Sound 3 volume edits

Schema-1 hash-bound edit plans now accept:

```json
{"operation": "set_sound3_volume", "value": 21}
```

The value is an integer raw code from 0 to 63. Bools, floats, strings and values
outside that range fail. The operation sets all 16 Sound 3 cells in Pattern 1
uniformly, including existing parameter-only cells. It does not accept sound,
pattern or step arguments. Public APIs are `calibrated_sound3_volumes(frame)`
and `set_calibrated_sound3_volume(frame, value)` in `po33_re.formats.volume`.

The accepted context requires the tested owner-0 Sound 3 window 11716..19716 and
the established backing-buffer layout. Sound 3 note steps 1/2/5/9/13 must retain
their observed auxiliary keys F0/FF/F1/F6/FF and nonvolume parameters; other Sound 3
cells must retain the observed parameter-only layout. Unknown pitch bits, other
parameters, keys, note placement or sample windows fail. Other sounds and unrelated
bytes are preserved literally. Source volume values may differ by step: the measured
middle ramp is read exactly rather than averaged or retroactively marked uniform.

The field is bits 6–11 of the little-endian first two primary bytes. Only first-byte
0xc0 and second-byte 0x0f masks change. All auxiliary values, samples, other sounds,
other patterns, globals and unrelated bits remain unchanged. Source files remain
immutable and compilation requires a fresh output directory.

Whole native bodies at physical codes 0/18/21/36/63 are reproduced independently.
Both generated interior values restore exactly and change repeated-tone amplitude
in the expected opposing directions with pitch and loop stable. The 0..63 policy
uses those six value bits and observed endpoints; it does not claim individual
hardware verification of every integer, a percent/dB curve, numeric UI scale or
that code 0 means silence. Only uniform Sound 3 / Pattern 1 editing is enabled.
Existing note-key and cell-copy operations retain their prior context guards.

Public compiler replay plans reproduce both accepted WAVs byte-for-byte:

- `experiments/replay-sound3-volume18-plan-001/plan.json`
- `experiments/replay-sound3-volume36-plan-001/plan.json`

Use `python -m po33_re apply-edits ARTIFACT --plan PLAN --out-dir FRESH_DIRECTORY`.
Project JSON remains a read-only view; it is not an edit-plan input. Compiler reports
remain hardware-unverified, even when their bodies and WAVs match accepted controls.

- [Lower-interior physical result](generated-sound3-volume18-results.md)
- [Upper-interior physical result](generated-sound3-volume36-results.md)
- [Volume module](../src/po33_re/formats/volume.py)

All **853 regression tests pass**, including 52 focused volume/plan checks. The
[public workflow validation](../experiments/sound3-volume-public-plan-workflow-validation-001.json)
binds current physical evidence, both accepted WAV replays and the fresh persistence
registration. Tests cover all 64 raw codes for software preservation, genuine
endpoint/interior bodies, unknown-layout rejection, stale hashes and immutable sources.
