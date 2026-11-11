# First generated pattern: hardware validated

The user explicitly confirmed that the generated restore and expected four-note playback
worked. The supplied backup now matches the entire generated packet body exactly,
with all511 checksums valid, unchanged samples, unchanged other patterns and complete
source rows at Steps1/5/9/13. See
[hardware validation](../experiments/edited-pattern-001/hardware-validation.json).
The software validation report remains a record of checks performed before hardware testing.

The user explicitly reports recording this backup **after playback**, rather than the
original planned ordering. The comparison still matches the complete native body with
no masking, alignment correction or metadata normalization. No playback-induced native
differences were observed for this capture. See
[capture context](../experiments/edited-pattern-001/capture-context.json).
The initial hardware observation is retained as the historical report made before the
backup was supplied. The next control is [changing one melodic key](melodic-key2-control.md).

The original test procedure below is retained for provenance.

Restore **experiments/generated-pattern-four-001/restore-four-notes.wav** using the same
stereo playback path and levels that worked for the trim and sample candidates. It is
44.1kHz PCM16, approximately23.1seconds. Enter receive mode with **write + sound + record**
and play the whole file.

The candidate retains the recorded Sound3 note at Pattern1 Step1 and copies its complete
raw event rows to **Steps5,9,13**. All samples, sound settings and other patterns are
unchanged. It should produce **four evenly spaced short tones per16-step loop**.

1. Report whether restore completes successfully.
2. **Before playing the pattern**, keep Pattern1 selected, TONE, write off, playback
   stopped and **Sound8** selected. Record a full stereo backup with the same settings to
   **experiments/edited-pattern-001/capture.wav**.
3. After saving that backup, play **Pattern1** for one or two loops. Report whether you
   hear four evenly spaced short tones, then stop playback. Leave the four-note pattern
   in place afterward.

Taking the backup before sequencer playback keeps the protocol comparison independent
of any playback-state changes. If you inspect the step lights, select Sound3, enter write
mode without pressing numbered keys, check1/5/9/13, exit write mode and reselect Sound8
before capturing. Step-light inspection is optional.

Button combinations and pattern playback follow the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en). Restore replaces the
device state; the original one-note backup remains in **experiments/event-007-b-melodic/capture.wav**.
If restore or playback fails, report the behavior and retain the settings for diagnosis.

Software evidence:

- [Candidate validation](../experiments/generated-pattern-four-001/software-validation.json)
- WAV SHA-256: `222f4ff71d54fcda6175d64adef00d67c64f452eee43cc3041bb5f49e677ca26`
- Expected native body SHA-256: `8b39765df9a4caf71e509f54b0c49e2f0d95ad1a60f4effa46daa687259d0104`
- Exactly511 packets, frame end89396, full phase/count roundtrip and exact target body.
- Only Pattern1 data packet indices4/5/6/7 change; samples and other patterns are preserved.
- The same writer reproduces the independent corrected joint kick recording exactly.

This candidate's restore and expected playback are user confirmed, and recapture comparison
passes exactly. It copies opaque note rows rather than
decoding or changing pitch, duration, sound selection or auxiliary bitfields.
The full suite passes **244 tests in69.17s**. Coverage includes the genuine melodic WAV,
exact corrected-joint reproduction, chunk boundaries, occupied-target rejection and CLI
input preservation. Ruff lint and formatting checks pass for all89 Python files.

The prepared `scripts/validate_pattern_recapture.py` requires a real WAV and its reviewed
decoded artifact before writing a hardware validation report. Three focused validator
tests pass: accepting the software target as a comparison vector, rejecting an unedited
backup, and rejecting a sample change even with valid checksums and four populated steps.
Those three tests used software comparison vectors. A new genuine-WAV regression now
independently decodes the after-playback backup and verifies the complete native body.

Reproduce the candidate in a fresh directory:

```powershell
.\.venv\Scripts\python.exe scripts/make_pattern_candidate.py experiments/event-007-b-melodic/derived/analysis-001/capture.symbols.npz --out-dir experiments/generated-pattern-four-002
```

The reusable CLI operation produces a new phase artifact and report, without playing it:

```powershell
.\.venv\Scripts\python.exe -m po33_re clone-step experiments/event-007-b-melodic/derived/analysis-001/capture.symbols.npz --pattern 1 --source-step 1 --target-steps 5 9 13 --out cloned.symbols.npz --report cloned.report.json
```
