# Staggered-coordinate investigation, round 3

The round 2 tail mapping now has an algebraic explanation in the accepted waveform
model. A reversible diagnostic representation removes constant relative phase from
late tails. The substantial earlier differences remain, so this is not a payload decoder.

## Derivation

The existing encoder selects its component signs using
`I_index=floor(t+0.625)` and `Q_index=floor(t-0.125)`.
At cycle midpoint `t=n+0.5`, those indices are `n+1` and `n` respectively.
Group the coordinates into a diagnostic cell:

```text
cell[n] = (high[n+1], low[n])
circular_index: 10 -> 0, 11 -> 1, 01 -> 2, 00 -> 3
increment[n] = (index[n+1] - index[n]) modulo 4
```

The observed mapping `A.high[n]=NOT B.low[n-1]`, `A.low[n]=B.high[n+1]`
becomes `A.cell[n]=(NOT B.cell[n].low, B.cell[n].high)`.
That advances this defined circular index by one. Thus a constant mapped tail has
identical increments, without a capture-specific fitted shift or inversion. This
derivation concerns component coordinates; it does not prove a physical carrier
rotation of the complete waveform or the device's protocol bit assignment.

For N original labels, grouping produces N-1 cells. The initial high coordinate and
final low coordinate must be retained. Increments produce N-2 values and require
the first circular index to reconstruct cells. With these explicit boundaries, both
transformations are reversible. None of these values is exported as a verified state image.

## Capture results

Report: ../experiments/staggered-probes-001.json. Input order is empty event-002-a,
Steps 1/2/3 event-001-b/event-002-b/event-003-b and repeated Step 1 event-004-b-repeat.
All ten channel inverses recover the original absolute-label arrays exactly, including
their differing endpoint counts. Original files are untouched.

The report lists every constant relative-phase run of at least 64 cells. For each
comparison with empty state, only the initial unchanged prefix and final constant-offset
tail qualify; no additional long constant interval was found in the intervening region.
Phase offsets below are `(variant - empty) modulo 4` in the defined circular index.

| State | Constant tail starts at cell | Left/right offset | Changed increments, left/right |
| --- | --- | --- | --- |
| Step 1 | 126937 | 0 / 3 | 88256 / 88575 |
| Step 2 | 126937 | 0 / 3 | 88167 / 88248 |
| Step 3 | 938283 | 3 / 3 | 699622 / 696192 |
| Step 1 repeat | 126937 | 0 / 3 | 88256 / 88575 |

The last changed increment is 126936 for Steps 1/2 and 938282 for Step 3, on both
channels. Cell/increment indices have different definitions from original label indices;
these are not updated state-field offsets. The original Step 3 onset prediction remains
failed. No symbol or endpoint was discarded to make a strict capture comparison pass.

This identifies where a *constant* relative relationship begins. It does not establish
an abrupt modulation-state switch at that location: before it, the relative phase varies
densely, and the underlying data may differ. The tail starts are not verified packet,
checksum or pattern boundaries.

## Remaining coding probes

For each populated state/channel, XOR and modulo-four subtraction of increments were
tested in [20000,21024), split into 512 training and 512 holdout coordinates on each
binary lane. None supports a recurrence of degree <=32. Fitted degrees are 255-257;
holdout error counts are 238-271. This excludes only the tested small linear models,
not all scrambling, compression, coding or serialization.

The next software investigation can use this reversible representation to examine the
remaining changed spans and differential component serialization. A verified payload
representation, validation rules and controlled edited restore are still prerequisites
for writable pattern fields. No new recording is required for this result.

## Reproduction and verification

```powershell
.\.venv\Scripts\python.exe scripts/staggered_probes.py experiments/event-002-a/derived/analysis-001/capture.symbols.npz experiments/event-001-b/derived/analysis-001/capture.symbols.npz experiments/event-002-b/derived/analysis-001/capture.symbols.npz experiments/event-003-b/derived/analysis-001/capture.symbols.npz experiments/event-004-b-repeat/derived/analysis-001/capture.symbols.npz --out experiments/staggered-new.json
```

Eight focused tests passed (five new staggered tests and three previous framing tests).
Checks include a hand-specified circular-order vector, exact inverses with retained
boundaries, the independently constructed coordinate mapping, run boundaries and invalid
short input. Ruff lint and formatting pass. The full suite was not rerun for this
research-only addition; production decoding and encoding were unchanged.

## Subsequent serialization probes

Round 4 tests word serialization and cumulative XOR/modular feedback on raw and reassociated
views across all three edited positions. No tested transform localizes the changed regions.
See serialization-investigation.md and ../experiments/serialization-probes-001.json through
003 for candidate bounds, independent holdouts and positive controls. An independent
component-transition decode is the next preferred software investigation.
