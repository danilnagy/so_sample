# Step 2 kick A/B/A

The user supplied all three requested recordings for the same kick (Sound 9, slice key 1)
at Pattern 1, Step 2. All are 44.1 kHz, 16-bit stereo at the established reduced level,
with no clipping. Source hashes, measured metadata and planned/observed action distinctions
are recorded beside each capture. Originals remain untouched.

Threshold 0.0063 yields 1,970,367 labels per channel for A and returned A. These match
exactly, including counts, on both channels. The empty A is also exactly equal to the
empty A from event-001, with no alignment, remapping or discarded symbols.

B has 1,970,366 left and 1,970,367 right labels. The one extra A left label is value 1 in
the ending constant carrier run and remains an explicit endpoint difference.
Compared with A, B has 88,122 changed left labels and 1,471,410 changed right labels.
Both channels first change at index 9405. Left changes end at 126936; right extends to
1970366. Removing the event restores the entire baseline exactly.

Step 1 first changed at 9309; Step 2 at 9405. The observed shift is 96 phase labels,
equivalent to 24 packed-label bytes per channel. These units are not state-image bytes.
Comparing the two populated states gives changes from 9309 through 76734 left / 76735
right; their later streams match each other over the shared span despite differing from
the empty baseline. This further argues for examining transport coding before assuming
that the whole changed region contains step fields or sample modifications.

## H2: candidate step-related spacing

Hypothesis: for the same kick and this selected UI/device state, moving the event one step
advances its first transport divergence by 96 labels per channel. This is based on only two
positions and is not a confirmed record size, payload field, or writable offset.

Pre-registered independent prediction: Step 3 would first differ at index 9501 on both
channels, if the candidate spacing continues. Event-003 is prepared to test that prediction
with a fresh empty A, a kick at Step 3, and an empty returned A. Differences elsewhere and
all endpoint counts must also be retained. A failed prediction must be recorded rather
than adjusting the formula or alignment until it fits.

Tracked comparison: event-002-comparison-summary.json. Derivations use the established
absolute-label convention, with threshold and hashes pinned in the fixture manifest.
No checksum, scrambling, compression, framing or musical-state field is identified.
