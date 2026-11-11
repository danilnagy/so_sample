# Copy-based Sound3 return confirmed

Copying the retained Sound8 over Sound3 reproduces every complete phase label and both
channel counts of the original untrimmed Sound3-copy capture. The user supplied the
requested capture and replied "done", without a reported deviation. Exact hardware
actions remain user-reported, not independently observed.

The original source is preserved at empty-001-h-sound3-copy-return/capture.wav, SHA-256
`cbcec520586e91ba48b46b4e05fbca58b6b6eaf392974a592ef6a8b7641da7ee`.
Stereo44.1 kHz PCM16 inspection finds24.793 seconds, unclipped peaks0.1681/0.1609.
Decoder0.2 at threshold0.0063 produces178922 complete left labels and178921 right labels.
Independent amplitude-clock checks have zero label or quarter-sign disagreements in
the compared interior[43,178874), including the metadata tail.

## Registered return

The unchanged registration is ../experiments/sound3-copy-return-predictions-001.json;
evaluation is ../experiments/sound3-copy-return-results-001.json.

- Maximum-to-copy first change177148 on both channels passes the exact saved window.
- Count growth+1 left,0 right passes the saved allowance.
- All six reference anchors remain unchanged at their original positions.
- Last nonzero increment178792 on both channels matches the original reference.
- Both saved original-prefix hashes[0,178795) match exactly.
- More strongly, full complete-label arrays match original E exactly, with no unequal
  counts, shifted comparisons, rewritten arrays, phase rotations or trimmed tails.

This completes a controlled return to the original transmitted content after the minimum
and maximum trim procedures. It supports a repeatable effect on the candidate Sound3
metadata region and a copy-based return path. It does not decode a native trim value,
sample codec, pointer, checksum or editable state field. The earlier maximum-knob return
remains failed. The source WAVs themselves are distinct recordings and are not byte-equal.

## Existing-data coding follow-up

A fresh primary-source review identified a concrete related-device lead:
[libpo32 protocol](https://github.com/ericlewis/libpo32/blob/3b3a0a758ba452fc809027c5bafcc5e2d0931532/core/docs/PROTOCOL.md).
Its CRC-driven additive whitening is tested as a hypothesis against the minimal empty
capture. None of2304 enumerated candidate streams yields a16-byte varied encoded run
for constant plaintext0 or255, despite testing all65536 starting states. See
related-whitening-investigation.md for the finite search, positive controls and limits.
No new PO-33 decoder is inferred from the PO-32 implementation.

The next missing observation is ordinary playback of the retained tone in this cleared
series. The earlier playback belonged to the old memory-full state; it does not measure
this newly recorded full tone. That observation can establish audible duration/frequency
and recording quality, without another parameter change or backup. See
minimal-tone-playback-control.md. Played duration still cannot establish native sample
length or codec rate until note/pitch and native encoding are verified.

Reproduction:

```powershell
.\.venv\Scripts\python.exe scripts/check_clean_copy.py experiments/sound3-copy-return-predictions-001.json --out experiments/sound3-copy-return-results-new.json
```

The genuine-capture return is pinned and independently re-decoded in focused regression
checks. Whitening positive controls use an independent standard-library CRC computation,
corrupted continuation and constant-carrier rejection. Ruff checks pass. No new full-suite
result is claimed.
