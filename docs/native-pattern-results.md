# Native pattern controls

The existing captures can now be compared after checksum-validated packet decoding.
Each of16 patterns has a selector0xA041 and five0xC498 data packets, concatenating to
**1032 bytes**. The currently observed layout supports a768-byte primary region, a
256-byte auxiliary region and an8-byte opaque footer.

For the intended Sound9/slice1 kick in Pattern1:

| Control | Primary offset | Identical12-byte region | Auxiliary offset | Value |
| --- | ---: | --- | ---: | ---: |
| Step1 | 24 | `cff683000000000000000000` | 776 | 16 |
| Step2 | 72 | same | 792 | 17 |
| Step3 | 120 | same | 808 | 16 |
| Joint Step1+2 | 24,72 | same at each | 776,792 | 16,16 |

This establishes a **48-byte primary step stride** and **16-byte auxiliary step stride**
for these controls. Four12-byte primary regions per step are reported as raw regions;
their general allocation and packed field meanings remain unknown. Sound, pitch, volume,
timing, effects and the auxiliary values are not assigned decoded semantics.

Starting from the controlled empty native frame, moving Step1's primary region and entire
auxiliary row to Step3 reproduces the genuine whole plain packet list and encoded body
exactly. Inserting that same raw pair at Steps1/2 also reproduces the corrected joint
capture's whole packet list and encoded body exactly. This is a **retrospective
reconstruction after inspecting the captures**, not a preregistered or hardware test.

The Step2-only reconstruction fails at auxiliary offset792: predicted16, actual17.
This difference is retained, and the intended identical slice is not treated as proof of
identical actual key/parameter state. Old phase-domain predictions and their failures
also remain in the original reports. The corrected joint artifact is used only after
checking its source WAV hash against the fixture manifest; the archived wrong upload
is excluded.

Evidence and reproduction:

- [Native control analysis](../experiments/native-pattern-controls-001.json)
- `scripts/native_pattern_controls.py` reproduces the analysis to fresh outputs.
- The genuine-control regression tests preserve the observed Step2 auxiliary difference.

Inspect any supported pattern frame without editing it:

```powershell
.\.venv\Scripts\python.exe -m po33_re inspect-patterns experiments/edited-sample-001/derived/analysis-001/capture.symbols.npz --out pattern-report.json
```

The latest hardware-verified sample recapture has Pattern1 bytes exactly equal to the
controlled empty pattern. It can serve as the baseline for the
[next single melodic note capture](melodic-step1-control.md), avoiding a new empty recording.
Pattern writing and audible sequence behavior still require their own hardware tests.

The later [Sound3 melodic control](melodic-step1-results.md) refines the raw structure to
16 three-byte sound-indexed cells plus16 auxiliary bytes per step. Sound3 uses cell2;
Sound9 uses cell8. The old12-byte groupings remain diagnostic subdivisions. Packed note
bitfields are still unknown. The new opaque-step writer has reproduced the genuine joint
kick body exactly; its first [generated pattern restore](native-pattern-restore-test.md)
copies the recorded melodic step to create four notes. The user confirms successful restore
and expected playback; the after-playback recapture now matches the generated body exactly,
with unchanged samples and all511 checksums valid.
The current full suite passes **244 tests in69.17s**, including the genuine sample
recapture, raw kick controls, malformed pattern layouts and CLI input preservation.
Ruff lint and formatting checks pass for all89 Python files.
