# Framing investigation, round 2

The populated-state repeat confirmed deterministic absolute phase labels for the tested
Step 1 state. A new diagnostic now explains much of the long divergence through a
simple relationship between staggered phase-sign coordinates. Payload decoding remains
unresolved. No original WAV, symbol artifact or restore waveform was modified.

## Evidence

Report: ../experiments/framing-probes-002.json. Input order is empty event-002-a,
Step 1 event-001-b, Step 2 event-002-b, Step 3 event-003-b. Source and artifact hashes
are recorded. Earlier report 001 preserves the initial density/channel-lag probes.

For each pair and channel, 200 candidate mappings were searched in the fixed training
window [1000000,1004096): optional coordinate swap, separate high/low lags from -2 to
+2 and four inversion masks. The selected candidate was tested in independent window
[1800000,1804096). Every pair/channel had one unique perfect training candidate and
4096/4096 matching holdout symbols.

Besides identity, the only selected mapping was:

```text
A.high[n] = 1 XOR B.low[n-1]
A.low[n]  = B.high[n+1]
```

Here A and B are the earlier/later input of the pair. These are sign coordinates of
absolute phase labels, not established protocol bits. The opposite lags matter: this
is not simply shifting a whole stream or rotating each label independently.

| Comparison | Left mapping | Right mapping | Last mapped difference, left/right |
| --- | --- | --- | --- |
| Empty vs Step 1 | Identity | Swap/invert/stagger above | 126936 / 126936 |
| Empty vs Step 2 | Identity | Swap/invert/stagger above | 126936 / 126936 |
| Empty vs Step 3 | Swap/invert/stagger above | Swap/invert/stagger above | 938283 / 938283 |
| Step 1 vs Step 2 | Identity | Identity | 76734 / 76735 |
| Step 1 vs Step 3 | Swap/invert/stagger above | Identity | 938283 / 938283 |
| Step 2 vs Step 3 | Swap/invert/stagger above | Identity | 938283 / 938283 |

Full-span diagnostic comparisons exclude two endpoint symbols at each end to support
all candidate lags. This exclusion is explicit in the report; strict original channel
lengths and comparisons remain alongside it. No stored artifact is normalized or trimmed.
Steps 1/2 match the empty state for over 1.84 million trailing symbols under the selected
mapping; Step 3 matches for over 1.03 million. Earlier regions still differ substantially.
Applying the late mapping globally also introduces prefix differences; it is not an
accepted whole-stream decoder.

## Interpretation and limits

Large absolute-label differences extending to the end do not necessarily mean changed
encoded payload throughout that span. These exact coordinate relationships provide a
stronger explanation for the late tails than an unspecified scrambling/cipher claim.
The previous recurrence/rank tests measured differences in raw absolute coordinates;
their negative results remain valid for those mappings, but cannot exclude simple coding
after a verified phase interpretation.

Whether this relationship reflects modulation state, decoder grouping or a protocol
transformation is unverified. The mapping was discovered from the same finite capture
set, then checked on separate windows; those windows are not new independent captures.
No checksum, packet length, state field or encryption algorithm is established. The
failed Step 3 exact-onset prediction remains failed under its original definition.

The next useful software investigation is to derive the relationship from the staggered
waveform model and determine where its coordinate state changes. A candidate interpretation
must preserve original data and pass independent controls before producing editable
payload. Additional hardware recordings are not required for this finding.

## Reproduction and verification

```powershell
.\.venv\Scripts\python.exe scripts/framing_probes.py experiments/event-002-a/derived/analysis-001/capture.symbols.npz experiments/event-001-b/derived/analysis-001/capture.symbols.npz experiments/event-002-b/derived/analysis-001/capture.symbols.npz experiments/event-003-b/derived/analysis-001/capture.symbols.npz --out experiments/framing-new.json
```

Three focused tests passed: an independently constructed staggered mapping, a corrupted
holdout, unrelated random streams and unequal endpoint accounting (the first test
contains both exact and corrupted holdout checks). Ruff lint and formatting pass.

## Follow-up

Round 3 derives the mapping as a constant quarter-turn in reassociated component
coordinates and verifies a lossless inverse across all five captures. See
staggered-investigation.md. Earlier nonconstant spans remain unresolved; no payload
decoder or artifact normalization has been adopted.
