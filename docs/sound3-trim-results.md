# Sound3 trim: registered location and size checks passed

The user supplied the requested minimum-length capture and replied "done", without a
reported deviation. The original WAV is retained at empty-001-f-sound3-trim-min/capture.wav,
SHA-256 `09d7f911938ac6c4c21264db92c894db40895b2b18ea6ca324c345ac7eac7d70`.
Hardware actions remain user-reported; the original TONE mode was inferred from prior
protocol rather than independently observed.

Stereo44.1 kHz PCM16 inspection finds24.867 seconds, unclipped peaks0.1681/0.1609.
Decoder0.2 at threshold0.0063 yields178922 complete labels on both channels, partial
final intervals left[0],right[1]. Independent amplitude-clock validation finds zero label
and all-four-quarter disagreements over left[43,178874),right[44,178874).

The unchanged registration is ../experiments/sound3-trim-predictions-001.json;
its evaluation is ../experiments/sound3-trim-results-001.json.

- Both channels first differ at177147, inside the predicted Sound3 window[177131,177172).
  All preceding complete labels match the prior Sound3-copy capture, including the large
  shared sample-region content. This is transport-content preservation, not parsed PCM.
- Count growth is0 left,+1 right, inside the saved-12..12 allowance for terminal carrier.
- The last nonzero staggered increment remains178792 on both channels, as predicted.
- All six128-increment anchors remain unchanged at their original positions.

The trim setting affects the candidate inline Sound3 region, supporting the location
hypothesis. It does not expose a single writable native field: raw differences include
1212 labels left and1362 right across the rest of the tail. No edited restore is generated.

## Tail coding follow-up

../experiments/sound3-trim-structure-001.json preserves strict raw, reassociated phase and
increment comparisons. Increment differences begin177146 left,177145 right and end178792
on both channels. After phase index178793, relative phase is constant0 left,1 right.
That explains why right raw labels continue to differ through the carrier suffix; it
does not identify a checksum, cipher, packet terminator or decoded zero data.

Twenty bounded binary recurrence probes cover raw XOR, phase XOR/mod4 difference and
increment XOR/mod4 difference, with high/low coordinates for both channels. Training
span[177200,178224) and separate holdout[178224,178736) were chosen after observation.
Every fit exceeds degree256 during training, so no candidate reaches holdout validation.
This is a larger bound than the earlier32-degree probes, but still excludes only these
finite difference models. Plaintext constancy in the metadata tail is unverified.

Next restore Sound3's trim length with knob B at its maximum and capture once, testing
whether the original serialization returns. The original untrimmed reference is pinned
separately; matching only the anchors or size will not count as an A-return. Exact full
complete-array equality and carrier endpoint differences are also reported separately.
See sound3-trim-return-control.md. Maximum knob position may encode a different endpoint
than the original default, so failure would not by itself prove a bad capture.

Reproduction:

```powershell
.\.venv\Scripts\python.exe scripts/check_clean_copy.py experiments/sound3-trim-predictions-001.json --out experiments/sound3-trim-results-new.json
.\.venv\Scripts\python.exe scripts/trim_structure.py experiments/empty-001-e-copy-to-3/derived/analysis-001/capture.symbols.npz experiments/empty-001-f-sound3-trim-min/derived/analysis-001/capture.symbols.npz --out experiments/sound3-trim-structure-new.json
```

Focused genuine-capture checks and a synthetic corrupted-return-prefix guard cover the
new evidence and return evaluator. Existing clean-copy checks are retained. Ruff checks
pass; no new full-suite claim is made.
