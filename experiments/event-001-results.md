# Single kick event: A/B/A results

Target confirmed by the user: empty Pattern 1, Step 1, Sound 9, slice 1, a recognizable kick.
The user supplied the three recordings requested for adding and removing that event.
Exact button-by-button actions and full UI metadata were not independently supplied.

All recordings are 44.1 kHz, 16-bit stereo. Peaks remain around 0.168/0.161; no clipping.
At explicit threshold 0.0063, A and B contain 1,970,367 labels per channel. Returned A has
1,970,357 per channel. Its entire shared span equals A exactly, without shifts or remapping.
The ten extra A labels per channel are all label 1 within the terminal constant carrier run.
Changing returned-A threshold to 0.004 and 0.003 did not recover them or change the overlap.
This is an explicit endpoint difference, not a declaration of full-file equality. It does
not appear to affect the differing event region; the exact physical end framing is unverified.

Adding the kick changes both channels beginning at zero-based phase-symbol index 9309.
Left has 88,307 changed labels, ending at index 126936. Right has 1,471,718 changed labels,
extending to the terminal region. B versus returned A gives the same changes within their
shared span. This is a reversible association with the reported edit, not a confirmed field.

Exploratory angular phase deltas and adjacent label-coordinate XOR do not collapse the
changes to a small field. Angular delta differences: 88,232 left / 1,701,414 right.
Coordinate XOR differences: 88,241 left / 1,470,119 right. These are transport-label
transforms, not established descrambling or protocol-bit recovery. Coding, checksums,
serialized UI state and other interpretations remain alternatives. No pattern-byte offset,
checksum, encryption or compression is inferred from the size of these differences.

Tracked reports: event-001-comparison-summary.json and event-001-phase-transforms.json.
Source hashes are in each capture's inspection/experiment records and fixture manifest.
Full strict changed ranges and symbol artifacts are stored under the relevant capture's
ignored derived/analysis-001 directory. Original recordings are unchanged.

Next: repeat with the same kick at Step 2 in Pattern 1 using a fresh A/B/A series. Compare
return reproducibility and the onset/extent of changes across independent step positions
before proposing a state-field mapping. Do not modify decoded state data yet.
