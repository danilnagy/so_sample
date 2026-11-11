# DEVELOPMENT.md — PO-33 Backup Reverse Engineering

> **Historical document.** This is the implementation brief the research started from in
> October 2026, kept as written with dated status notes. It includes the original prompts
> given to the AI coding assistant. For the current state of the project see the
> [README](README.md); for the verified format, the [format reference](docs/format-reference.md).

Implementation brief for a Python research project in Visual Studio Code on Windows 11 or macOS.

Prepared: 2026-10-07  
Status updated 2026-10-08: the Phase0 hardware roundtrip gates are complete. Native packet
framing, a zero-start trim edit, fixed-size sample replacement and bounded pattern
copy/key/removal edits have been validated against hardware recaptures. Read-only
project export is available; nonzero-start samples and broader fields remain under investigation. See
[current status](README.md#status) and [packet evidence](docs/packet-decoding.md).
The original implementation brief below is retained as the initial Phase0 contract.

Update 2026-10-11: the research program is complete and the web app (sosample) has started
in `web/`; see [README](README.md) and the [web app proposal](docs/web-app-proposal.md).
The TypeScript core's fixtures come from `scripts/export_web_fixtures.py`; rerun it after a
new verified session is added to its GOLDENS list.

Keep this file beside `README.md`. The README explains the goal; this document defines the first implementation, commands, tests, and evidence required to move forward.

## 1. First deliverable

Build a small command-line toolkit that can inspect genuine stereo backup recordings, preserve their modem symbols, reconstruct transfer audio, and compare controlled experiments.

The first usable version must:

1. Inspect a recording without modifying it.
2. Decode a recording twice and produce identical symbol artifacts.
3. Reconstruct audio while preserving the captured transport content.
4. Explain any differences after decoding the reconstructed audio.
5. Produce byte/bit difference reports for comparable artifacts.
6. Record a manual hardware restore result separately from software test results.

The long-term goal remains a desktop sample and pattern editor. Do not implement the GUI or arbitrary sample replacement in this first phase.

## 2. Evidence and terminology

Use these distinctions throughout the code and documentation:

| Term | Meaning |
| --- | --- |
| Capture | Original stereo PCM WAV recorded from the PO-33 |
| Symbol stream | Per-channel sequence of demodulated phase symbols |
| Packed symbols | Reversible byte packing of those symbols for storage |
| Transport payload | Data recovered after verified phase interpretation, synchronization, and framing |
| State image | Device state representation after any remaining coding, validation, or compression |
| Project model | Editable samples, patterns, and settings derived from understood state fields |

**A file named `.bin` is not automatically a state image.** Differences in packed symbols may reflect phase interpretation, alignment, or decoding errors rather than musical state.

### Source review

The following references were reviewed on 2026-10-07. Pin actual Git commits during implementation; these branch links can change.

- [Official PO-33 guide](https://teenage.engineering/guides/po-33/en), section 8: describes stereo sound/pattern backups and restoration. Transmit uses **write + sound + play**. Receive uses **write + sound + record**. Restore erases samples and patterns when transfer starts.
- [cspotcode/PO-33-KO-backup-re](https://github.com/cspotcode/PO-33-KO-backup-re): an earlier investigation of the waveform. Its README reports a 7,800 Hz oscillator with four phase states and cites 8-bit µ-law audio at 23,437.5 Hz. Treat the internal sample representation as a lead requiring independent verification.
- [sZXZ/po33-experements README](https://github.com/sZXZ/po33-experements/blob/main/README.md): documents conversion and reconstruction scripts, including `po33_converter.py` and `po33_reconstitute.py`. A documented restore workflow is not proof of hardware acceptance in our environment. Its receive-button shorthand differs from the official guide.
- [Upstream data-format notes](https://github.com/sZXZ/po33-experements/blob/main/PO33_DATA_FORMAT.md): describes interleaved left/right bytes containing four phase symbols per byte, least-significant pair first.
- [Upstream pattern notes](https://github.com/sZXZ/po33-experements/blob/main/PO33_PATTERN_STRUCTURE.md): proposes pattern/step structures while acknowledging uncertain decoding. Treat offsets and field interpretations as hypotheses.
- [Upstream decoder](https://github.com/sZXZ/po33-experements/blob/main/po33_converter.py): its amplitude threshold uses raw integer units across PCM widths; mono input is duplicated; interleaving stops at the shorter channel. Audit these behaviors before adopting the implementation.
- [Upstream encoder](https://github.com/sZXZ/po33-experements/blob/main/po33_reconstitute.py): defaults to 48 kHz, 16-bit stereo, prepends a carrier, and iterates with lookahead. Audit prefix handling and final-symbol preservation.

The initial engineering work should investigate these limitations. It must not assume that reported scrambling is established, or that phase symbols are already correctly interpreted as protocol bits.

## 3. Development environment

Use Python **3.12** for the initial reproducible environment. This is a project choice, not a claim that it is the newest Python.

Use VS Code with the Microsoft Python extension. If using full Visual Studio instead, open the same folder and choose the same virtual environment; the Python package and commands remain the same.

Required local tools:

- Python 3.12
- Git
- VS Code
- A recorder capable of capturing two independent audio channels
- A true stereo input and stereo 3.5 mm connection for device captures

A laptop headset microphone socket is often mono. Confirm the input channels before relying on it.

### Windows PowerShell

Create a project folder and open it:

```powershell
New-Item -ItemType Directory -Path po33-re
Set-Location po33-re
git init
py -3.12 -m venv .venv
code .
```

After creating the package files described below:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip freeze > requirements-lock.txt
.\.venv\Scripts\python.exe -m po33_re --help
.\.venv\Scripts\python.exe -m pytest
```

These commands do not require virtual-environment activation or a PowerShell execution-policy change.

### macOS terminal

```bash
mkdir po33-re
cd po33-re
git init
python3.12 -m venv .venv
code .
```

After creating the package files:

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pip freeze > requirements-lock.txt
.venv/bin/python -m po33_re --help
.venv/bin/python -m pytest
```

If `code` is unavailable, open the folder through VS Code's File menu.

Choose **Python: Select Interpreter** and select this project's `.venv`. Run all subsequent commands from the repository root. Command examples below use `python` to mean this selected environment's interpreter.

Keep dependency-resolution results with the experiment provenance. A freeze file records the installed environment; it is not a portable, hash-verified dependency lock.

## 4. Proposed files and ownership

Create these files in stages rather than filling every module with placeholder implementations.

| Path | Responsibility |
| --- | --- |
| `pyproject.toml` | Packaging, dependencies, test configuration |
| `src/po33_re/__init__.py` | Package version |
| `src/po33_re/__main__.py` | Calls the CLI entry point |
| `src/po33_re/cli.py` | argparse commands and exit codes |
| `src/po33_re/audio.py` | WAV validation, PCM loading, channel statistics |
| `src/po33_re/artifacts.py` | Schema validation, hashes, provenance, safe writes |
| `src/po33_re/modem/symbols.py` | Symbol arrays and reversible packing |
| `src/po33_re/modem/decode.py` | Demodulation and diagnostics |
| `src/po33_re/modem/encode.py` | Waveform synthesis from explicit transport artifacts |
| `src/po33_re/analysis/diff.py` | Comparison metrics and changed ranges |
| `src/po33_re/analysis/alignment.py` | Candidate alignments, with explicit evidence |
| `src/po33_re/analysis/entropy.py` | Sliding-window entropy, after basic diffs work |
| `src/po33_re/formats/state.py` | Future verified state parser; defer initially |
| `tests/test_audio.py` | Generated PCM and invalid-input fixtures |
| `tests/test_symbols.py` | Packing, channel order, partial-symbol preservation |
| `tests/test_diff.py` | Independent expected difference results |
| `tests/test_transport.py` | Synthetic codec tests |
| `tests/test_captures.py` | Genuine capture integration tests |
| `tests/fixtures/manifest.json` | Capture identity, hash, expected results |
| `experiments/<id>/experiment.json` | Device actions and capture setup |
| `experiments/<id>/capture.wav` | Immutable original recording |
| `experiments/<id>/derived/` | Versioned analysis output |
| `docs/transport.md` | Verified waveform/framing notes |
| `docs/field-map.md` | Hypotheses and confirmed field mappings |
| `docs/upstream-audit.md` | Commits, licenses, behavioral audit |
| `.vscode/settings.json` | Interpreter/test discovery settings |
| `.vscode/launch.json` | Module debugger configuration |

Add `__init__.py` to each Python subpackage. Keep capture, symbol, transport, and state types distinct.

### Initial pyproject.toml

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "po33-re"
version = "0.0.1"
description = "Research tools for PO-33 stereo backup transfers"
requires-python = ">=3.12,<3.13"
dependencies = [
  "numpy>=1.26,<3",
  "scipy>=1.12,<2",
  "soundfile>=0.12,<1",
]

[project.optional-dependencies]
dev = [
  "pytest>=8,<10",
  "ruff>=0.6,<1",
]

[project.scripts]
po33 = "po33_re.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
markers = [
  "capture: requires a genuine PO-33 recording fixture",
]

[tool.ruff]
target-version = "py312"
line-length = 100
```

Use standard-library `argparse`, `json`, `hashlib`, and `pathlib`. Add plotting only when needed. Do not introduce a µ-law dependency until the audio representation is verified.

### __main__.py

```python
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

Implement `cli.main(argv: list[str] | None = None) -> int`. Do not leave an apparently working decode command that writes fake binary output. Unsupported commands must return an explicit error.

### VS Code settings.json

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["tests"],
  "files.exclude": {
    "**/__pycache__": true,
    ".pytest_cache": true
  }
}
```

### VS Code launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "PO-33: inspect baseline",
      "type": "debugpy",
      "request": "launch",
      "module": "po33_re",
      "args": [
        "inspect",
        "experiments/baseline-001/capture.wav"
      ],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

### Initial .gitignore

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
build/
dist/
*.egg-info/
experiments/**/*.wav
experiments/**/*.bin
experiments/**/*.npz
experiments/**/derived/
```

Keep experiment metadata and fixture manifests in Git. Store raw captures separately with immutable hashes and a second copy. Include small synthetic fixtures in Git where practical. Do not redistribute captured sample content without considering its source.

## 5. Audit upstream tools before porting

Clone both research repositories outside the package implementation, for example under an ignored `reference/` directory:

```bash
git clone https://github.com/sZXZ/po33-experements.git reference/po33-experements
git clone https://github.com/cspotcode/PO-33-KO-backup-re.git reference/PO-33-KO-backup-re
git -C reference/po33-experements rev-parse HEAD
git -C reference/PO-33-KO-backup-re rev-parse HEAD
```

Add `reference/` to `.gitignore`. Record exact commits and license findings in `docs/upstream-audit.md`. Check licensing before copying source; public availability alone does not establish permission to redistribute code.

Initially run the documented upstream entry points unchanged on copies of recordings:

```bash
python reference/po33-experements/po33_converter.py experiments/baseline-001/capture.wav experiments/baseline-001/derived/upstream.bin
python reference/po33-experements/po33_reconstitute.py experiments/baseline-001/derived/upstream.bin experiments/baseline-001/derived/upstream-reconstructed.wav
```

Create the output directory first. These are experimental reference commands, not acceptance criteria.

Inspect:

- PCM width, signedness, amplitude scaling, and channel validation.
- Leading silence and sync acquisition.
- Absolute versus differential phase interpretation.
- Independent channel alignment and symbol count.
- Partial groups of symbols at the end.
- Added or duplicated preambles.
- Last-symbol handling and silent truncation.
- Whether a successful exit means valid data or merely file creation.

Wrap reference scripts through explicit arguments using the selected Python executable; avoid shell command construction. Preserve logs and hashes. Keep reference behavior separate from corrected behavior.

## 6. CLI contract

**The following commands are interfaces to implement. They are not existing tools.**

| Command | Purpose |
| --- | --- |
| `po33 inspect capture.wav --json report.json` | WAV metadata and channel diagnostics |
| `po33 decode capture.wav --out capture.symbols.npz --report decode.json` | Lossless channel-symbol artifact and diagnostics |
| `po33 encode capture.symbols.npz --out restore.wav --report encode.json` | Experimental waveform reconstruction |
| `po33 export-symbols capture.symbols.npz --channel left --out left.bin` | Packed symbols for analysis |
| `po33 export-symbols capture.symbols.npz --channel right --out right.bin` | Independent right-channel artifact |
| `po33 compare a.bin b.bin --json diff.json --xor diff.xor.bin` | Strict offset comparison |
| `po33 roundtrip capture.wav --out-dir derived/run-001` | Software decode/encode/decode and comparison |

Implement `inspect` and `compare` first. Then implement symbol artifacts, decode, encode, and software roundtrip.

Command behavior:

- Do not play audio or operate hardware automatically.
- Refuse to overwrite existing output unless `--force` is supplied.
- Refuse an output path that aliases an input, including symlink aliases.
- Treat missing or malformed input as an error.
- Send diagnostics to stderr; keep JSON machine-readable.
- Return 0 when the requested operation completes, 2 for CLI/input errors, and 3 for processing failure or a failed roundtrip check.
- `compare` returns 0 for a completed report even if files differ. Include `identical: false`.
- An encoder can write a waveform without knowing whether hardware will accept it. Its report must state `hardware_verified: false`.

## 7. Audio and symbol artifacts

### Capture inspection

For each channel report sample rate, PCM subtype, frames, duration, peak amplitude, RMS, possible clipping, and channel similarity.

Load PCM as normalized floating point for signal processing so thresholds do not depend on 16-bit versus 24-bit integer magnitude. Retain the original file and its format metadata.

Initially require stereo PCM WAV. Reject mono, more than two channels, empty input, non-finite samples, and unsupported encoding. Never silently duplicate mono.

Capture at a native stereo rate supported by the interface. Start with 44.1 or 48 kHz PCM; record the exact choice and preserve it. Neither rate is a claimed exclusive protocol requirement.

### Lossless symbol artifact

Use an NPZ containing:

- `left_symbols`: uint8 values 0–3.
- `right_symbols`: uint8 values 0–3.
- `metadata_json`: schema/version/provenance as a Unicode scalar.

Load with `allow_pickle=False`. Validate array dimensions, symbol values, and schema.

Metadata must identify the phase convention, decoder version, source SHA-256, channel order, sample rate, detected boundaries, symbol counts, discarded samples, uncertainty, and any transformations.

Preserve unequal channel lengths. Do not silently shorten both streams. If an encoder cannot handle a mismatch, fail and explain it.

For a packed-symbol export, define four successive two-bit values per byte with the first value in the lowest pair. Record symbol count and padding in a sidecar. Packing round trips must preserve incomplete groups; raw byte equality is insufficient when counts differ.

Never use an entropy jump alone as proof of a header or pattern boundary.

## 8. First comparison implementation

`analysis.diff.compare_bytes(a: bytes, b: bytes) -> dict` should return:

- Both lengths.
- Overlapping length.
- Changed byte count in the overlap.
- Changed bit count in the overlap.
- Percentage of overlapping bytes changed; null when overlap is empty.
- Non-overlapping tail length.
- Contiguous changed ranges using **zero-based, end-exclusive** offsets.
- Whether both files are identical.

XOR output covers the overlapping region only. Report tails separately; do not invent zero padding.

Independent reference case:

```text
A hex: 00 01 02 FF
B hex: 00 03 02 FE 99

overlap bytes: 4
changed overlap bytes: 2
changed overlap bits: 2
changed percentage: 50.0
extra tail bytes: 1
changed ranges: [1, 2), [3, 4)
XOR hex: 00 02 00 01
identical: false
```

First test:

```python
from po33_re.analysis.diff import compare_bytes

def test_known_diff():
    result = compare_bytes(
        bytes.fromhex("00 01 02 FF"),
        bytes.fromhex("00 03 02 FE 99"),
    )
    assert result["overlap_bytes"] == 4
    assert result["changed_overlap_bytes"] == 2
    assert result["changed_overlap_bits"] == 2
    assert result["changed_overlap_percent"] == 50.0
    assert result["tail_bytes"] == 1
    assert result["changed_ranges"] == [[1, 2], [3, 4]]
    assert result["identical"] is False
```

Also test identical files, empty inputs, one empty input, boundary changes, and unequal lengths with an identical prefix.

Keep strict comparisons separate from candidate alignment. Alignment reports must show shift, evidence, retained span, and discarded regions. Do not optimize alignment until files look equal.

## 9. Test plan and what each result proves

| Test | Required evidence | What it proves |
| --- | --- | --- |
| PCM validation | Generated stereo fixtures, mono rejection, width/rate cases | Correct audio ingestion |
| Symbol packing | Known vectors plus incomplete groups | Reversible storage |
| Diff tests | Hand-calculated changes and tails | Correct comparison arithmetic |
| Same-file decode | Two independent runs, equal symbols | Determinism for one input |
| Synthetic modem tests | Known symbols, transitions, channel order, endpoint cases | Software codec consistency |
| Genuine capture tests | Fixed capture hashes and reviewed expected output | Regression against real signals |
| Software roundtrip | Decode → encode → decode, documented boundaries | Transport preservation within software |
| Original capture restore | Manual device checklist | Recording/playback path works |
| Generated restore | Manual checklist plus re-capture | Hardware accepts reconstruction |

Synthetic encode/decode agreement can hide a shared bug. Add independent vectors or compare against reference tools. Include all 16 adjacent phase transitions, first/last symbols, leading/trailing silence, inverted polarity, both supported rates, and simulated clock mismatch as development progresses.

Do not equate PCM waveform equality with data equality. Captures can differ acoustically while representing identical symbols.

Missing real fixtures must be **skipped with a reason**, not reported as passed. Keep the hardware result `not_run` unless a person performs it. Automated tests must not claim to restore a PO-33.

Basic checks after implementation:

```bash
python -m pytest -m "not capture"
python -m pytest -m capture
python -m ruff check src tests
```

Fix meaningful failures; do not broaden tests simply to increase the test count.

## 10. First recording and hardware validation

Preserve existing work before resetting or clearing anything. Use a disposable, documented state for experiments.

### Capture

1. Connect PO-33 line-out to a verified stereo input.
2. Disable automatic gain, noise suppression, EQ, and other processing.
3. Start recording with a short lead-in.
4. Transmit using **write + sound + play**.
5. Record the complete transfer and a short tail.
6. Save the untouched PCM WAV and SHA-256.
7. Capture at least two additional transfers without intentional device changes.

Do not trim the only copy, normalize it, convert it to mono, or use a lossy codec.

### Establish the playback path

Before testing a generated file, verify that the **original recording** restores through the same output/interface/cable. Keep a separate untouched backup.

Connect stereo output to PO-33 line-in. Enter receive with **write + sound + record**, then play the complete file. Restoration replaces current content.

Determine playback level empirically using the original recording. Document OS volume, interface level, and device behavior; do not assume maximum volume improves reliability.

### Validate reconstruction

After software roundtrip checks, restore the generated recording to the disposable state. Check all populated sample slots, drum slices, patterns, audible settings, and known global settings. Back up the restored device again.

Record `accepted`, `rejected`, or `inconclusive`, together with observations. A successful receive indication alone is weaker evidence than matching musical behavior and an analyzed re-capture.

If reconstruction fails while the original succeeds, investigate the transport. Do not start patching pattern bytes.

## 11. Experiment metadata

Save `experiment.json` beside every immutable capture. Example values below are illustrative; replace them with observed values.

```json
{
  "schema_version": 1,
  "id": "baseline-001",
  "created_at": "2026-10-07T11:00:00Z",
  "baseline_id": null,
  "device": {
    "model": "PO-33",
    "firmware": "unknown",
    "sync_mode": "observed value"
  },
  "state": {
    "description": "Disposable controlled state; list every known sample and pattern",
    "tempo_bpm": 120,
    "selected_pattern": 1,
    "selected_sound": 9,
    "playing": false,
    "swing": "observed value or unknown"
  },
  "changes": [],
  "actions": [
    "Describe how the state was established",
    "Start recorder",
    "Press write + sound + play"
  ],
  "capture": {
    "path": "capture.wav",
    "sha256": "REPLACE_WITH_ACTUAL_HASH",
    "interface": "REPLACE_WITH_DEVICE_NAME",
    "sample_rate_hz": 48000,
    "channels": 2,
    "pcm_subtype": "PCM_24",
    "processing": "none"
  },
  "hardware_restore": {
    "status": "not_run",
    "observations": []
  }
}
```

Keep UI identifiers 1–16. Convert to zero-based indexes only inside explicitly documented code.

A pattern event must describe **both sound slot and note/slice key**. “Sound 9 at step 1” alone does not completely specify what should play.

First controlled event:

- Pattern 1.
- Step 1.
- Sound slot 9.
- Drum slice key 1.
- No intentionally recorded effects or parameter changes.

Capture A unchanged, B with this event, and A again after removing it. Confirm the return to baseline through device behavior. Record selected-sound and selected-pattern changes because they may themselves be serialized.

First compare repeated unchanged captures. Distinguish signal/decoder instability from repeatable state differences before interpreting musical edits.

## 12. Sample investigation after transport validation

Use finite, AC signals such as tone bursts, spaced impulses, chirps, and seeded noise with known duration.

The analog input path can filter, resample, clip, or shift the source. A source WAV is therefore not an exact byte oracle for internal storage. Constant DC and byte ramps may not survive AC coupling or ordinary playback hardware.

Begin with locating reproducible sample-related changes and length/allocation metadata. Verify codec and sample rate independently before implementing extraction or insertion.

Do not promise replacement until payload coding, allocation, metadata, and validation fields are sufficiently understood. Preserve unknown regions unchanged.

## 13. Implementation sequence

### Session 1 — package and observation tools

- Create packaging, CLI entry points, and VS Code configuration.
- Implement WAV inspection and strict binary comparison.
- Add meaningful generated-input tests.
- Clone and audit upstream tools.
- Create baseline capture metadata even if hardware recordings are not yet available.

Done when `inspect` and `compare` work, invalid input fails clearly, and the small unit suite passes.

### Session 2 — transport artifacts and decoder

- Define symbol schema and reversible exports.
- Reproduce reference decoding on a pinned recording.
- Add diagnostics for synchronization and each channel's length.
- Compare repeated decodes and repeated captures.
- Document unresolved boundaries and confidence.

Done when a real capture produces reproducible artifacts without silent data loss. If this is blocked, write the blocker and evidence.

### Session 3 — reconstruction

- Audit/reproduce the waveform generator.
- Verify symbol preservation using software tests.
- Validate preamble policy and final-symbol handling.
- Establish original-file hardware restoration.
- Test generated restoration manually and log the outcome.

Done when reconstruction is repeatedly accepted and its restored behavior matches the documented state. This requires the PO-33 and the user's manual observations.

### Session 4 — first field hypothesis

- Collect A/B/A event captures.
- Compare each channel and phase representation.
- Examine alignment/coding before inferring offsets.
- Add a field-map entry with experiments, representation, units, confidence, and alternative explanations.
- Confirm with multiple independent values and positions.

No field is “confirmed” because one changed byte looks plausible. Require repeatable correspondence; for writable fields, require successful controlled restoration.

## 14. Handoff prompt for a coding agent

Paste the following alongside README.md and this file:

> Implement Session 1 of DEVELOPMENT.md in this repository. Use Python 3.12, a src-layout package, and argparse. Build inspect and compare, safe output handling, JSON reports, and the specified meaningful unit tests. Preserve original recordings. Read the upstream repositories at pinned commits and record their licenses and audit findings. Keep modem symbols separate from decoded protocol/state data. Do not hardcode pattern offsets, invent checksums, or claim hardware verification. Unsupported decode/encode commands must fail explicitly until implemented. If no real recordings exist, complete the independent tools and state exactly which integration checks remain blocked. Run the relevant tests and report changed files, results, and unresolved questions. Continue later sessions only when their stated prerequisites are available.

## 15. First phase acceptance checklist

- [ ] Python environment and package installation are reproducible.
- [ ] Original recordings are preserved with hashes.
- [ ] Upstream commits, license findings, and limitations are recorded.
- [ ] Inspect detects invalid input and channel problems.
- [ ] Comparison handles lengths, bits, ranges, and tails correctly.
- [ ] Symbols retain channel order, exact counts, and partial groups.
- [ ] Decode results are deterministic on fixed inputs.
- [ ] Software reconstruction preserves the documented transport representation.
- [ ] Original recording restores through the chosen playback path.
- [ ] Generated recording restores, with behavior checked and re-capture preserved.
- [ ] Repeated unchanged captures establish a baseline for differential analysis.
- [ ] One controlled event has a complete action log and A/B/A captures.
- [ ] Every result distinguishes tested evidence from an upstream claim or hypothesis.

Until hardware restoration is demonstrated locally, the project remains an experimental transport toolkit.
