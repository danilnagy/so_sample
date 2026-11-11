# Serialization and feedback investigation, round 4

No tested serialization plus simple word feedback explains the dense changed regions.
The reversible phase representation from round 3 remains useful, but these additional
probes do not yield a payload decoder or editable pattern fields. No recording is requested
for this result; no original capture, symbol artifact or restore waveform was modified.

## Scope and selection

Reports ../experiments/serialization-probes-001.json through 003 compare empty event-002-a
with Steps 1, 2 and 3 respectively. Each pins source and artifact hashes. Every report
records 161280 candidate trials, 483840 total. Some trials are algebraically equivalent;
this is a count of enumerated trials, not distinct independent algorithms.

Each comparison covers:

- Three views: original labels, staggered circular phases, staggered phase increments.
- All 24 permutations of values 0..3 and four within-channel symbol packing offsets.
- Left-only, right-only, alternating stereo symbols and alternating packed channel bytes.
- Unsigned 1/2/4/8-byte words, both endiannesses for multi-byte words.
- XOR or modular subtraction of preceding words at lags 1/2/3/4/8/16/24/32/64/128.

Feedback is precisely `decoded_candidate[n] = word[n] XOR word[n-lag]` or
`(word[n] - word[n-lag]) mod 2**(8*width)`. These models could remove a cumulative XOR
or modular sum, if the input words and alignment were correct. The same label permutation
is used on both channels; independent per-channel permutations are not tested.

Each named view uses training window [20000,36384) and separate holdout [50000,66384).
Indices are in that view, not asserted to be identical original waveform positions.
For each view/layout/width/endian combination, the best candidate is selected using
training matching-word fraction alone; enumeration order breaks ties. The holdout is
then measured using that unchanged choice. There are 84 such selections per state.
Only complete groups/words inside these explicit analysis windows are packed. This is
not a trimming policy for any capture or decoder output.

## Results

The original training windows differ in approximately three quarters of phase values.
None of these candidate feedback transforms makes the edited states mostly match empty
state. The table takes the maximum across selected candidates for each word width.

| Edited position | Largest training match fraction | Largest 1-byte holdout fraction | Largest 2-byte holdout fraction |
| --- | --- | --- | --- |
| Step 1 | 0.8798% | 0.5628% | 0% |
| Step 2 | 0.7820% | 0.6200% | 0.0252% |
| Step 3 | 0.7572% | 0.6202% | 0% |

Selected 4- and 8-byte candidates have zero matching training and holdout words in all
three comparisons. Larger words naturally make incidental matches less likely; this is
not evidence for or against a particular cipher. Candidate multiplicity and selection
also prevent interpreting a small maximum as a significant correlation.

This rejects localization through the explicitly tested feedback/packing hypotheses in
these finite windows. It does not establish encryption, compression, a checksum, a
channel byte order or the absence of more complicated coding. The prefix remains
structured and the late-tail coordinate relationships from rounds 2/3 remain verified.

## Reference check and next investigation

A focused primary-source search again found the previously reviewed
[cspotcode waveform investigation](https://github.com/cspotcode/PO-33-KO-backup-re) and
[sZXZ conversion tools](https://github.com/sZXZ/po33-experements). This search did not
supply an independently validated PO-33 state decoder. Their phase/scrambling terminology
does not resolve the current local evidence; pinned-checkout audit limitations remain in
upstream-audit.md. No upstream implementation was copied.

The next useful task is an independent waveform-level component-transition decoder,
checking the quarter intervals the existing label artifact does not retain individually.
It should use synthetic known-input controls before any interpretation of genuine captures.
Further arbitrary packing searches or new step-position recordings are lower priority
until that modulation/serialization ambiguity is resolved.

## Reproduction and verification

```powershell
.\.venv\Scripts\python.exe scripts/serialization_probes.py experiments/event-002-a/derived/analysis-001/capture.symbols.npz experiments/event-001-b/derived/analysis-001/capture.symbols.npz --out experiments/serialization-new.json
```

Replace the variant with event-002-b or event-003-b to reproduce the other reports.
Eight focused tests passed: hand-calculated serialization order, four word-width cases
constructed with independent Python modular arithmetic, endian handling, an injected
feedback relation followed by a corrupted holdout, and invalid inputs. Ruff lint and
formatting pass. The full regression suite was not rerun for this research addition.

## Independent waveform follow-up

Round 5 recovers a clock from raw amplitude and samples all four quarter positions,
finding zero interior disagreements across five captures. This closes the proposed
component check for the tested states; it does not resolve payload serialization.
See waveform-investigation.md. The next requested control is a single combined Step 1
and Step 2 kick backup, with predictions pinned before capture.
