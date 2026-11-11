# Maximum trim length did not reproduce the original state

The supplied capture passes signal validation but fails the registered A-return prediction.
The failure is retained in ../experiments/sound3-trim-return-results-001.json; no prediction
window or original reference was changed. User confirmation was "done", with no reported
deviation; exact buttons and audible length were not independently observed.

The original WAV is preserved at empty-001-g-sound3-trim-return/capture.wav, SHA-256
`237230f9401b9be7093d306beaf38fbc139cc55dcfaf66570508d474d4e15119`.
Stereo44.1 kHz PCM16 inspection finds24.618 seconds, unclipped peaks0.1680/0.1609.
Decoder0.2 at0.0063 yields178921 complete labels per channel, partial intervals[1] on both.
Independent amplitude-clock checks have zero label and quarter-sign disagreements in
the compared interior[44,178874), including the changed metadata tail.

## Registered checks

- Minimum-to-maximum first change177147 on both channels passes the saved exact window.
- Complete-count growth-1 on each channel passes the saved-12..12 allowance.
- All six anchors remain at the same positions.
- The expected original prefix[0,178795) fails on both channels. Maximum differs from
  the original untrimmed state first at177148 on both channels, within the candidate
  Sound3 record, then densely through the remaining tail.
- Last nonzero increment is178791 left,178792 right. The saved178792 prediction therefore
  fails left and passes right. A last transition can disappear if its phase increment
  becomes zero; this one-position change does not establish a shorter payload or sample.

Matching size, location and anchors does not override the failed original-prefix check.
The maximum setting is a distinct serialized state in these captures. Its difference
could reflect a knob endpoint versus the copied default or other parameter/UI behavior;
this experiment does not establish an exact native endpoint value.

## Further software analysis

../experiments/sound3-trim-max-structure-001.json compares original to maximum in strict
raw, reassociated phase and increment views. Both raw arrays preserve[0,177148) exactly,
including the shared content region. After phase178793, relative phase is constant1 left,
0 right. Carrier phase explains the long left raw suffix difference; no source WAV or
artifact is rotated, aligned or trimmed.

The same twenty bounded binary-difference recurrence probes on this distinct endpoint
pair yield no supported degree<=256 model. This finite failure does not identify a cipher,
codec or checksum. No native trim-field patch or edited restore is produced.

The next return attempt copies the retained Sound8 over Sound3, so it tests the device's
copy operation instead of assuming that the maximum knob value equals the copied default.
It must still match the original prefix exactly; failure remains possible if copying
preserves destination settings or the retained source has changed. See
sound3-copy-return-control.md and the separately pinned registration.

Reproduction:

```powershell
.\.venv\Scripts\python.exe scripts/check_clean_copy.py experiments/sound3-trim-return-predictions-001.json --out experiments/sound3-trim-return-results-new.json
.\.venv\Scripts\python.exe scripts/trim_structure.py experiments/empty-001-e-copy-to-3/derived/analysis-001/capture.symbols.npz experiments/empty-001-g-sound3-trim-return/derived/analysis-001/capture.symbols.npz --out experiments/sound3-trim-max-structure-new.json
```

The genuine-capture regression preserves this failed return despite its passing location
and anchors. Existing clean-copy and synthetic corrupted-return checks remain in place.
Focused tests and Ruff checks pass; no new full-suite result is claimed.
