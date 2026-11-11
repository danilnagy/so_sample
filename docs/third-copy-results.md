# Sound3 copy: registered spacing predictions passed

The user supplied the requested copy8-to3 capture and replied "done", with no reported
deviation. The original source is retained at empty-001-e-copy-to-3/capture.wav, SHA-256
`a2d9672bd061bb9a8ea63af687164dda9e71a4c56d15d658b65d5c79d88af81f`.
Exact hardware actions remain user-reported, not independently observed.

The capture is stereo44.1 kHz PCM16,24.419 seconds, with unclipped peaks0.1681/0.1609.
Decoder0.2 at threshold0.0063 yields178922 complete left labels and178921 right labels.
Partial final intervals are left[0],right[1], retained separately. The one-label channel
count difference is not padded, discarded or used to force an encoder input.
Independent amplitude-clock validation finds zero disagreements in labels and all four
quarter signs over the explicitly compared interior[43,178874).

## Registered result

../experiments/third-copy-predictions-001.json remains unchanged. Reproducible evaluation
is ../experiments/third-copy-results-001.json, generated with check_clean_copy.py.

| Check | Saved prediction | Observed |
| --- | --- | --- |
| First raw change, left/right | Inline window[177131,177136) | 177133 /177132: passes |
| Competing front-table window | [43290,43299) | Fails |
| Relative complete-count growth | 20..36 inclusive | 22 /21: passes |
| Last nonzero increment, both channels | 178792, displacement+28 | Exactly178792: passes |
| Three128-increment anchors per channel | Same positions90000/120000/150000 | All six pass |

The observed first-change positions are exactly40 after the Sound2-copy first changes.
The terminal nonzero increment advances28, as predicted independently before upload.
This supports the candidate40-position populated-reference spacing and28-position
replacement growth. Under the proposed replacement model their difference is12 for an
empty record; a native12/40 field layout is still not parsed or independently established.
These values are waveform transport coordinates, not asserted payload byte counts.

All complete labels before177132 match the saved before-state, so the earlier large
shared content region survives this copy. Complete-count growth differs from28 because
the constant carrier endpoint is shorter. No tail is trimmed or called decoded zero data.

## Adjacent-record template probe

../experiments/copy-record-structure-001.json tests candidate adjacent40-position regions
starting177090..177093 in raw, reassociated-phase and increment views, on both channels.
None of24 channel/view/window combinations yields equality under any of the24 value
permutations. These short post-observation probes reject literal templates in those
windows only. They do not establish encryption, coding, exact record boundaries or
the absence of other representations. No native parameter or writable checksum is known.

The next useful control changes one parameter of the copied sound while retaining the
stored source. A minimum-length trim on Sound3 tests whether the candidate record owns
the trim setting, without another analogue recording. See sound3-trim-control.md and
the separately saved predictions. No edited restore has been generated.

Reproduction:

```powershell
.\.venv\Scripts\python.exe scripts/check_clean_copy.py experiments/third-copy-predictions-001.json --out experiments/third-copy-results-new.json
.\.venv\Scripts\python.exe scripts/copy_record_structure.py experiments/empty-001-e-copy-to-3/derived/analysis-001/capture.symbols.npz --out experiments/copy-record-new.json
```

Five focused clean-copy checks pass, including independent Sound3 re-decode and a
deliberately wrong terminal prediction that fails despite a passing location window.
Ruff lint/format checks pass. No new full-suite result is claimed.
