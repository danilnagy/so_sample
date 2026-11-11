# Measured-clock recovery

The alternating-key hardware recapture exposed a timing limitation in the existing
sign-crossings decoder. At the reviewed0.0063 threshold, native parsing fails at wire
byte13130, tag0xC498. Independent amplitude-clock diagnostics find the first left-label
disagreement at26472 and widespread later misalignment, while the right channel agrees
throughout its checked span. The failed artifact and report are preserved at
[initial failure](../experiments/edited-note-key-001/initial-decode-failure.json).

The new **amplitude-clock-0.1** method samples the waveform on its measured quarter clock
instead of accumulating independently rounded sign-run lengths. It uses the existing
fourth-harmonic amplitude estimator. A unique alignment is selected from512 bounded
quarter/prefix combinations using **2048 pre-frame labels only**, at reference positions
0..127. That training region ends before the native frame begins. No target packet
content, body hashes or CRC outcomes select alignment or correct labels.

Both recovered channels pass every interior four-quarter relation. Native parsing then
validates all511 packets through the final marker. Only afterward is the result compared
to the generated target: the full encoded body and every plain packet match exactly.
The body SHA-256 is
`91b37d61e3bc71de72748dfd846892e62a7d839a9332f13a6f9c56687cdeadf0`.
This recapture verifies the observed Sound3 key1/2 edit, together with the user's explicit
alternating-pitch playback report. See
[hardware validation](../experiments/edited-note-key-001/hardware-validation.json).

The method also recovers the exact previously established bodies of all24 eligible
source-WAV-matched captures in packet-corpus-002, with **56,090** checksums and zero failed
frames. Those counts include equivalent repeats, not independent hardware tests.
See [clock corpus](../experiments/amplitude-clock-corpus-001.json). This validation compares
hashes only after decoding; the existing bodies are never inputs to recovery.

Original WAVs, crossing artifacts and failed attempts remain unchanged. The default
`decode` command is unchanged; `decode-clock` is a separate experimental command.

```powershell
.\.venv\Scripts\python.exe -m po33_re decode-clock experiments/edited-note-key-001/capture.wav --acquisition experiments/edited-note-key-001/derived/analysis-001/capture.symbols.npz --out recovered.clock.npz --report recovered.clock.json
```

The new artifact covers only the fixed measured-clock window, retaining an explicitly
inherited acquisition prefix. It contains all required frame labels but leaves unobserved
capture edges. It is therefore marked **partial_clock_window** and direct waveform
encoding rejects it. A new waveform must be built from its checksum-verified packet
frame with the explicit canonical packet ending. No captured ending is inferred, padded
or truncated to pass encoder checks.

The recovery tests include independent analytic waveforms at44.1/48k with later reference
labels intentionally corrupted, genuine reproduction of the original failure and recovered
target, acquisition identity checks, direct-encode rejection and CLI source protection.
The genuine test also confirms that an explicit verified-packet rebuild is encodable.
The full suite passes **244 tests in69.17s**. Ruff lint and formatting checks pass for
all89 Python files. The separate corpus run recovered all24 source-matched frames.

A second physical recording, the [key16 endpoint control](melodic-key16-results.md),
also parses exactly with this method after the crossing decoder fails at byte17902.
No expected field value guides recovery. The failed acquisition and successful clock
artifact are retained separately, with a genuine-WAV regression for both outcomes.
