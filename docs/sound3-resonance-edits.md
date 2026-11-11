# Bounded uniform Sound3 resonance edit plans

Schema-1 hash-bound plans accept:

```json
{"operation": "set_sound3_resonance", "value": 32}
```

Only integer raw codes **0,32,63** are supported. Each has complete generated
reception and ordinary-audio evidence at fixed low-pass16. The B32 component is
between B0 and B63 under both frozen5% margins; the measured response is not
proportional to raw code. No all-integer range, Q argument or UI unit is exposed.
Bools, floats, strings and all other codes are rejected.

APIs are `calibrated_sound3_resonances(frame)` and
`set_calibrated_sound3_resonance(frame,value)` in `po33_re.formats.resonance`.
Targets set all16 Sound3/Pattern1 cells uniformly, including parameter-only cells.
Source guards require the tested owner0 backing layout and Sound3 window11716..19716,
cutoff16/pitch14/volume36 throughout, unknown first-byte bit5 clear, and the known
note steps1/2/5/9/13 and keysF0/FF/F1/F6/FF. Resonance values must be uniform at one
of the three observed codes, or the specific earlier note32/parameter0 vector.
Other automation mixtures, codes, parameters, keys, notes and windows fail.

Only third-primary bits2..7 change. Cutoff's low-two bits, pitch, volume, auxiliary
keys, samples, globals and every other state bit remain exact. The earlier cutoff,
pitch and volume writers retain their guards; untested combined plans can fail.
This operation does not imply that bit7 has the same general role in every layout.

Public replay plans are:

- `experiments/replay-sound3-resonance0-plan-001/plan.json`
- `experiments/replay-sound3-resonance32-plan-001/plan.json`
- `experiments/replay-sound3-resonance63-plan-001/plan.json`

All three entire accepted bodies and WAVs replay exactly. Compile with
`python -m po33_re apply-edits ARTIFACT --plan PLAN --out-dir FRESH_DIRECTORY`.
Source artifacts stay immutable; project JSON is read-only. Compiler reports
remain `hardware_verified:false` even when their outputs match accepted restores.

All1,137 regression tests pass, including whole independent bodies, observed-code
guards, known legacy layout, unknown automation rejection, sample/window/key guards,
source hashes, extra arguments and WAV replay checks. The next
[saved-FX probe](pattern1-FX-probe-control.md) investigates a separate pattern region;
no public FX writer is enabled.

- [Interior resonance evidence](generated-sound3-resonance-middle-results.md)
- [Endpoint pair evidence](generated-sound3-resonance-pair-results.md)
