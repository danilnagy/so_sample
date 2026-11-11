# Clean Sound2 copy control completed

The fresh before/after pair isolates copying Sound8 into empty Sound2. The user replied
"done" to the requested protocol; no deviation was reported. Exact button actions are
user-reported, not independently observed. Source WAVs and the original deviated capture
are retained unchanged.

Both captures are stereo 44.1 kHz PCM16, unclipped, with peaks around0.168/0.161.
Decoder0.2 at threshold0.0063 produces178868 complete labels per channel before,
178900 after. Independent amplitude-clock checks have zero label or quarter-sign
disagreements over the explicitly compared interior spans. Incomplete terminal intervals
remain separate and are not trimmed to make an encoder input.

## Registered results

The unchanged registration is ../experiments/clean-copy2-predictions-001.json;
the reproducible evaluation is ../experiments/clean-copy2-results-001.json.

- Fresh before matches every complete label of the original Sound1/Sound8 state.
  All registered prefix hashes and six anchors therefore satisfy applicability.
- First strict change is177093 left,177092 right. The registered inline window
  [177085,177121) passes; the competing front-table window[43278,43287) fails.
- Relative complete-count growth is32 per channel, inside the registered0..128 range.
- All six128-increment anchors remain unchanged at their original positions.
- Clean after matches all complete labels of the earlier recovery capture. That older
  experiment still has its reported extra operations and remains observational.

These results support the location prediction for this clean copy operation. They do
not establish a general native field table, allocation pointer, sample codec or checksum.
The earlier proposed12-label slot spacing is not a verified front-table layout.

## Endpoint and tail follow-up

../experiments/copy-tail-structure-001.json records an additional observation. The last
nonzero staggered phase increment is178708 in Sound8-only,178736 in Sound1/Sound8,
and178764 in Sound1/Sound2/Sound8, on both channels. Each copy therefore moves this
empirical boundary by28. Complete-count growth differs because the constant carrier
section has different lengths: the first copy adds21 complete labels, the second32.
No native payload terminator or internal data length is inferred from that boundary.

Searching diagnostic tail offsets-128..128 in raw, reassociated-phase and increment
views finds no varied exact run longer than12 values after177121. Long matches there
are constant carrier runs; they are excluded from content-reuse evidence. This does
not identify a simple relocatable descriptor in the changed tail. No patch is generated.

A candidate can nevertheless be tested independently: empty-slot spacing12, and a
populated reference record40, whose replacement growth would be28. It predicts the
next destination3 change about40 positions after the destination2 change, with another
28-position movement of the last nonzero increment. These are transport hypotheses,
not parsed byte sizes. The new registration and single-capture instructions are in
../experiments/third-copy-predictions-001.json and third-copy-control.md.

## Reproduce and verify

```powershell
.\.venv\Scripts\python.exe scripts/check_clean_copy.py experiments/clean-copy2-predictions-001.json --earlier-after experiments/empty-001-d-copy-to-2/derived/analysis-001/capture.symbols.npz --out experiments/clean-copy2-results-new.json
.\.venv\Scripts\python.exe scripts/copy_tail_structure.py experiments/empty-001-b-tone/derived/analysis-001/capture.symbols.npz experiments/empty-001-c-copy-to-1/derived/analysis-001/capture.symbols.npz experiments/empty-001-copy2-clean-a/derived/analysis-001/capture.symbols.npz experiments/empty-001-copy2-clean-b/derived/analysis-001/capture.symbols.npz --out experiments/copy-tail-new.json
```

Three focused checks pass: genuine independent re-decode/pinned results, rejection of
model interpretation after before-state geometry changes, and preservation of protocol
deviation ineligibility. Ruff lint/format checks pass. The last full suite was154 tests
before the later recovery and clean-copy checks; it was not rerun for this analysis.
