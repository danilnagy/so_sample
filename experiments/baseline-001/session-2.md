# Session 2 results

See [transport notes](../../docs/transport.md) for interpretation, commands and limitations.

Original recording hash verified unchanged. Two independent decodes created byte-identical
NPZ artifacts. The symbol streams are unequal: left 2,004,469, right 2,004,468.
Both channel exports preserve those counts in mandatory JSON sidecars, including three
left padding symbols. Incomplete final cycle signs are separately recorded in metadata.
Explicit reference comparison matches all 1,002,234 bytes retained by the upstream converter.
The left symbol dropped by upstream remains stored in our artifact.

Outputs: derived/session-2-001/capture.symbols.npz, capture-repeat.symbols.npz, decode.json,
decode-repeat.json, determinism.json, reference-comparison.json, left.bin(.json), right.bin(.json).
These derived files are excluded from Git. Capture hash and decoder expectations are tracked
in tests/fixtures/manifest.json.

61 tests passed; lint and formatting checks passed. No repeated-recording comparison,
waveform reconstruction or generated hardware restoration is claimed. Early noise acquisition
and nominal clock uncertainty remain explicit research questions.
