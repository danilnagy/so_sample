# Bounded tempo preset edit plans

The edit-plan operation `set_tempo_preset` accepts the integer 80, 120 or 140:

```json
{"operation": "set_tempo_preset", "bpm": 80}
```

It uses the same hash-bound plan schema and fresh output directory as the other edits:

```powershell
.\.venv\Scripts\python.exe -m po33_re apply-edits experiments/event-032-a-return-tempo-120/derived/analysis-001/capture.symbols.npz --plan experiments/replay-tempo80-preset-plan-001/plan.json --out-dir experiments/example-tempo80-preset-001
```

The observed field is zero-based payload offset129 in the second `0x7d5c` packet.
Native packet indices 1 and 2 must be the two 255-byte global records. Their opaque bytes
must match the recognized calibration hashes, with only the tempo byte masked out in
the second record. The current stored tempo must also be one of the three presets.
An already-selected target preset is a no-op. Unknown fields are never reset to a
template; matching hashes only validate context, and all unrelated bytes are retained.

The first record hash is
`c800383bf6f80b6589f84e447bf67e6dd61f6ac0984e855ad82a2a4913318674`;
the second record hash with byte 129 replaced by 0 is
`d83b81391c75f06328262d1b487bc2cd96cda3064e4335688f52f17e9cf3c0f4`.
These are layout guards, not decoding of other global fields. Different opaque global
settings, packet geometry, current fine-tempo values and arbitrary target BPM values
are rejected. Bool values, floats and strings are not integers for this interface.
The plan still binds the exact source artifact and complete native body.

Physical 120/140/80 captures and exact return establish the preset mapping. A generated
120-to80 restore matches the entire independent genuine 80 state and its displayed BPM.
The public compiler replay equals that accepted WAV byte-for-byte. See
[hardware results](generated-tempo80-results.md). Every compiler report remains
`hardware_verified:false`, and new edit combinations need appropriate evidence.

The API functions are `calibrated_tempo_preset(frame)` and
`set_calibrated_tempo_preset(frame, bpm)` in `formats/globals.py`. Project JSON remains
read-only; no arbitrary packet edits or general fine-tempo range are enabled by this
operation. The next [physical fine tempo 100 control](fine-tempo100-control.md) keeps
that boundary intact.

## Fine tempo is now supported separately

Endpoint/return controls and the generated137 restore support the guarded `set_tempo`
operation for integer60 to240. See [interface](tempo-edits.md) and
[results](generated-fine-tempo137-results.md). The original preset-only API retains its
three-preset contract; use the general operation for fine sources.
