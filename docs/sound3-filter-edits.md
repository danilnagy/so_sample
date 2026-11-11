# Bounded uniform Sound3 FILTER edit plans

Schema-1 hash-bound plans accept:

```json
{"operation": "set_sound3_filter", "value": 52}
```

Only integer raw codes **1, 16, 52, 62 and 63** are supported. These five codes have
independent physical backup evidence; generated16/52 also have exact restore and
listening confirmation. Intermediate codes, code0, bools, floats and strings are
rejected. There are no sound, pattern, step, frequency or percentage arguments.

| Raw code | Observed behavior in this control |
| --- | --- |
| 1 | Full counterclockwise low-pass; user could not hear sample |
| 16 | Partial low-pass; generated restore accepted and filtering heard |
| 52 | Partial high-pass; generated restore accepted and filtering heard |
| 62 | Full clockwise high-pass; user could not hear sample |
| 63 | Audible center, single middle tick; user reports no filter |

The operation sets all 16 Sound3/Pattern1 cells uniformly, including existing
parameter-only cells. APIs are `calibrated_sound3_filters(frame)` and
`set_calibrated_sound3_filter(frame, value)` in `po33_re.formats.filters`.

Source guards require the tested owner0 sample backing layout and Sound3 window
11716..19716, pitch14 with unknown first-byte bit5 clear, volume36 in every selected
cell, the established note steps1/2/5/9/13 and keysF0/FF/F1/F6/FF. Third-primary
high-six bits must retain the observed note/parameter layout, without labeling
them as resonance. Source filter codes must be among the five observed values;
raw0 is allowed only in parameter-only cells of the earlier unwritten layout.
It is reported literally and is not exposed as a target or interpreted as bypass.
Unknown source codes, parameters, keys, note positions or sample windows fail.

Only second-primary bits4..7 and third-primary bits0..1 change. Every other bit,
including pitch, volume, auxiliary values, samples, globals, other sounds and
patterns remains exact. Tests reconstruct all five complete physical bodies from
each supported uniform source. Public plans reproduce both accepted16/52 WAVs
byte-for-byte. Existing pitch and volume guards retain their prior restrictions;
untested combinations can be rejected.

Replay plans are:

- `experiments/replay-sound3-filter16-plan-001/plan.json`
- `experiments/replay-sound3-filter52-plan-001/plan.json`

Compile with `python -m po33_re apply-edits ARTIFACT --plan PLAN --out-dir FRESH_DIRECTORY`.
Source artifacts are immutable and project JSON remains a read-only view. Compiler
reports always retain `hardware_verified:false`, including accepted-WAV replays.

This is an observed-code policy, not an all-integer range. Contiguous branch
ordering is supported; complete field width, mode semantics, numeric UI units,
cutoffHz curve and broadband bypass are not established. The public plan returning
generated52 to the independently recorded center63 body is prepared; its hardware
reception is the next control.

All 1,025 regression tests pass, including35 new public FILTER checks for whole
physical bodies, both accepted WAVs, unsupported values, unknown contexts, source
hashes and extra arguments. Eight additional center-checker tests pass after the
full run with no later production changes.

- [Generated pair results](generated-sound3-filter-pair-results.md)
- [Next center restore](generated-sound3-filter-center-control.md)

The public-plan center63 restore is now physically accepted as its entire target
and every packet, with user-confirmed unfiltered playback. Scope and source guards
remain unchanged. See [center results](generated-sound3-filter63-results.md) and
the [next B-field probe](sound3-filter-B-probe-control.md). No resonance writer is
enabled; new third-byte contexts remain guarded.
