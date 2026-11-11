# Bounded uniform Sound3 pitch edit plans

Schema-1 hash-bound plans now accept:

```json
{"operation": "set_sound3_pitch", "value": 14}
```

The value is an integer raw code1..25, bounded by independent recorded endpoints.
The operation sets all16 Sound3/Pattern1 cells uniformly, including existing
parameter-only cells. Bools, floats, strings, code0 and values outside1..25 fail.
Sound, pattern and per-step arguments are unavailable. APIs are
`calibrated_sound3_pitches(frame)` and `set_calibrated_sound3_pitch(frame, value)`
in `po33_re.formats.pitch`.

Source context requires the tested owner0 Sound3 window11716..19716 and backing-buffer
layout, volume36 in every selected cell, the established note steps1/2/5/9/13 and
their keysF0/FF/F1/F6/FF, and the observed other primary parameters. Unknown bit5,
nonpitch parameters, keys, note positions, source volume or window fail. Source
pitch values must be within1..25; raw0 is accepted only at parameter-only cells
from the earlier unwritten layout. It is reported literally, not interpreted as
a note or a playable endpoint.

Only first-primary bits0..4 change. Bit5 and every other bit/byte, including volume,
keys, sample records, globals, other sounds and other patterns, stay exact. Full
physical bodies at1/13/14/25 are reconstructed independently. Both interior WAVs
replay byte-for-byte, and ordinary audio confirms a roughly one-semitone interval
for13→14 with unchanged loop timing.

The1..25 raw-code policy does not claim individual hardware calibration of every
integer or an exact semitone law across the whole range. No semitone argument or
numeric UI scale is exposed. Full field width remains unknown; bit5 is guarded
rather than overwritten. Existing volume and key/copy writers retain their prior
context guards, so untested combinations can fail.

Public replay plans:

- `experiments/replay-sound3-pitch13-plan-001/plan.json`
- `experiments/replay-sound3-pitch14-plan-001/plan.json`

Compile with `python -m po33_re apply-edits ARTIFACT --plan PLAN --out-dir FRESH_DIRECTORY`.
Source artifacts remain immutable and project JSON remains a read-only view.
Compiler reports remain hardware-unverified even when matching accepted WAVs.

All **917 regression tests pass**, including68 focused pitch/volume/plan checks.
Tests exercise all25 supported raw codes for literal software preservation,
independent physical bodies, bit5/unknown-context rejection, stale hashes, extra
arguments and both exact accepted WAV replays. A further37 FILTER/pitch checks
pass after the full run; no production writer changes follow those checks.

- [Physical interval results](generated-sound3-pitch-interval-results.md)
- [Native endpoint results](sound3-tone-pitch-range-results.md)
- [Next FILTER controls](sound3-filter-probe-control.md)
- [Public replay and handoff validation](../experiments/sound3-pitch-public-plan-and-filter-workflow-validation-001.json)
