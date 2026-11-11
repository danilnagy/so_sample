# Session 1 usage

DEVELOPMENT.md governs implemented command syntax and evidence requirements. README.md
contains the broader project vision; its binary commands and folder sketches are conceptual.

Python 3.12.15 is provisioned under ignored .tools/python; .venv is the project environment.
Dependencies are captured in requirements-lock.txt (an environment snapshot, not a portable
hash-verified lock). To recreate on a machine with Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Save the untouched stereo PCM recording at experiments/baseline-001/capture.wav.
Keep your second backup copy outside the repository. Then run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m po33_re inspect experiments/baseline-001/capture.wav --json experiments/baseline-001/inspection.json
.\.venv\Scripts\python.exe -m po33_re compare left-a.bin left-b.bin --json diff.json --xor diff.xor.bin
.\.venv\Scripts\python.exe -m pytest -m "not capture"
.\.venv\Scripts\python.exe -m pytest -m capture
.\.venv\Scripts\python.exe -m ruff check src tests
```

Reports are JSON; without --json they go to stdout. Existing outputs require --force;
input/output aliases are forbidden, including hard links. Output directories must already
exist. Compare reports differences with exit 0, with XOR covering only the overlapping bytes.
Inspection rejects non-stereo and non-integer-PCM recordings. Identical channels are flagged
in the report but not automatically rejected. Correlation alone does not prove correct stereo.

Record observed interface, sample rate, subtype, device state, actions, capture timestamp and
inspection SHA-256 in experiment.json. Pending fields must remain unknown until observed.
To register a genuine inspection fixture, add a captures entry to tests/fixtures/manifest.json
with path, sha256 and independently reviewed expected_inspection fields. No transport codec
is implemented yet: decode, encode, export-symbols and roundtrip return explicit failures.

The user has reported successful original backup/restores. This is prior hardware experience;
hardware_restore for baseline-001 stays not_run until this specific recording is restored and
its result documented. Generated reconstruction has not been tested.

## Validation result

On Windows with Python 3.12.15: 29 tests passed and one genuine-capture integration test
was skipped. Ruff lint and format checks passed. The Codex sandbox prevented pytest from
using its temporary directories; validation succeeded outside that sandbox with:

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp .tools/validation-final -p no:cacheprovider --tb=short -q
```

The package's comparison and output logic was written independently; no unlicensed upstream
implementation was copied. Real-capture decoding, symbol storage, software reconstruction,
and generated hardware restoration remain pending later sessions.

## Subsequent work

Session 2 now implements experimental decode and export-symbols. See [transport notes](transport.md) for current commands and validation. Session 3 also implements experimental encode and roundtrip; see [reconstruction notes](reconstruction.md).
