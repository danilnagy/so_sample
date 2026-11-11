# Experimental phase transport, Session 2

## Evidence and limits

`decode` now writes version-1 phase-symbol artifacts. These retain every demodulated
complete cycle on each channel, including unequal lengths and partial byte groups.
Lossless storage of these labels does not imply error-free demodulation of every physical
symbol, verified framing, or a parsed protocol/state image. No device fields are interpreted.
`encode` and `roundtrip` are now implemented experimentally; see [reconstruction notes](reconstruction.md). Candidate 001 was hardware-rejected; corrected 44.1 kHz candidate 002 was accepted according to the user. Behavioral checks and re-capture remain pending.

The current sign-crossings-0.2 decoder uses normalized floating-point PCM, a normalized threshold
of 10/32768 by default, interpolated zero crossings, nominal 7800 Hz carrier timing,
and rounded quarter-cycle sign runs. It searches independently per channel for the first
`11` candidate, consumes that pair, reinserts a 1, then reads the first two signs in each
complete four-sign cycle. Pair labels are 11=3, 10=2, 00=0, 01=1, preserving the reference's
absolute phase convention. Threshold is configurable with --threshold (strictly between
0 and 1). Changing it is a documented experiment, not automatic correction.

The vectorized implementation was written independently from the upstream scripts.
The initial negative-origin convention is explicit in metadata. No channel is duplicated,
interleaved or shortened during storage. Missing crossings or acquisition fail with exit 3.
Invalid input/schema/threshold and unsafe outputs fail with exit 2. Crossing gaps exceeding
one second fail instead of allocating long speculative sign runs. Malformed PCM and rates
below carrier Nyquist are rejected. No waveform samples are automatically trimmed.

Diagnostics include per-channel counts, first/last crossing positions, candidate acquisition,
unused source span, pre-acquisition sign bits, final incomplete-cycle signs, zero-length
intervals and rounding residuals. The residual is in quarter-cycle units, without the
additional scaling found in the TypeScript reference. Second-half signs are deliberately
interpreted as phase-transition portions; that interpretation remains a waveform hypothesis.
Leading/trailing noise can decode into spurious symbols. No silence-based trimming, drift
correction, frequency estimation or verified protocol synchronization has been implemented.

### Acquisition origin correction (0.2)

The earlier0.1 implementation inserted an implicit initial negative transition at file
time zero. A valid recording with a negative first significant sample after more than
one second of silence could therefore trip the long-gap guard on an invented interval.
Version0.2 places this approximate transition at the first thresholded sample instead.
Source samples are not trimmed; unobserved leading silence is not repeated as negative
sign bits. Metadata records the sample and origin policy. Real long crossing gaps still
fail. The existing phase convention and all reviewed complete-symbol goldens are unchanged.
Previously saved0.1 artifacts retain their historical decoder metadata and source hashes.

## Artifact and export

The NPZ contains `left_symbols` and `right_symbols` as one-dimensional uint8 arrays 0..3,
plus `metadata_json` as a Unicode scalar. Loading disables pickle. Schema, phase convention,
channel order, exact counts, source hash, decoder version and required diagnostics are checked.
Metadata and serialization have no run timestamp, allowing byte-identical repeated outputs.
The source recording remains the authority for all signal samples and uncertain boundaries.

Each export packs four values least-significant pair first and writes a `.bin.json` sidecar
with exact count, zero-padding count, channel, phase convention and hashes. For example,
[3,2,0,1,2] packs as hex 4b 02, with five symbols and three padding symbols.
`unpack_symbols` checks count, byte length and zero padding. Bytes alone do not distinguish
real final zero symbols from padding; preserve the sidecar. `compare` remains a strict raw
byte comparison, so consult counts before interpreting packed byte equality.

## Baseline 001 findings

Capture SHA-256: 6312a96c924ff3414b51584a1e86a2a950860b168d03cab9d735b2ed1d370370.
Original 44.1 kHz, signed 16-bit stereo file is unchanged. The user reports successful
original-file restoration; generated-file restoration has not been performed.

| Observation | Left | Right |
| --- | ---: | ---: |
| Complete decoded phase symbols | 2,004,469 | 2,004,468 |
| Export bytes (including padding) | 501,118 | 501,117 |
| Export padding symbols | 3 | 0 |
| Final incomplete-cycle sign intervals | 2 | 3 |
| Candidate acquisition sample | 277.32 | 289.00 |
| Crossing intervals with residual >0.25 | 106,225 | 107,570 |
| Fraction over threshold | 2.697% | 2.728% |

Candidate acquisition occurs around 6 ms into low-level lead-in noise. It is not a verified
start of transfer. The nominal-clock/no-trimming analysis agrees with upstream but should
not be presented as an error-rate measurement or reliable payload framing. Remaining source
samples after the last crossing are reported, not silently converted into extra symbols.

Two independent CLI processes produced identical NPZ files, SHA-256
1ac96b03699bce84b93f413315bcb484cafe4870f27f5e98972b25ea13c39b25.
A separate comparison deliberately reproduced upstream's complete-byte/shorter-channel
truncation: 1,002,234 interleaved bytes exactly match the pinned reference output,
SHA-256 027a504ff33b61e6333cc06232d2c402f5e5c214a32316f3f32173ecbfd8c92a.
One left symbol is excluded only for that comparison; it remains in our NPZ and export.
Full evidence and reports are under experiments/baseline-001/derived/session-2-001/.

## Commands

Run from the repository root. Create a fresh output directory for each experiment first.

```powershell
New-Item -ItemType Directory experiments/baseline-001/derived/my-decode
.\.venv\Scripts\python.exe -m po33_re decode experiments/baseline-001/capture.wav --out experiments/baseline-001/derived/my-decode/capture.symbols.npz --report experiments/baseline-001/derived/my-decode/decode.json
.\.venv\Scripts\python.exe -m po33_re export-symbols experiments/baseline-001/derived/my-decode/capture.symbols.npz --channel left --out experiments/baseline-001/derived/my-decode/left.bin
.\.venv\Scripts\python.exe -m po33_re export-symbols experiments/baseline-001/derived/my-decode/capture.symbols.npz --channel right --out experiments/baseline-001/derived/my-decode/right.bin
```

Existing outputs require --force. Input aliases and colliding outputs are refused.
Without --report, decode emits JSON to stdout; warnings go to stderr. Export sidecars
are always written as `<output>.json` and are included in overwrite protection.

## Validation and next evidence

61 tests pass on Windows/Python 3.12.15: packing and partial groups, schema/pickle rejection,
independent sign vectors with all 16 adjacent phase transitions, endpoints, amplitude and
PCM-width invariance, stereo order, safe CLI exports, existing inspection/comparison tests,
and genuine-capture inspection plus two independent decoder processes. The square sign
vectors use 249.6 kHz to give exact eight-sample quarter intervals. They test demodulation
logic, not bandlimited hardware waveforms at 44.1/48 kHz or an encoder's correctness.

Validation command used outside the Windows sandbox because pytest temp-directory access
was denied inside it:

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp .tools/session2-final-001 -p no:cacheprovider --tb=short -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Two additional recordings are now registered. At explicit threshold 0.02, captures 002/003
have identical channel streams, and capture 001 matches every shared symbol with one fewer
terminal symbol per channel. The default threshold also demodulates boundary noise and
fails strict repeated-recording comparison. See [repeated-capture findings](../experiments/repeat-capture-comparison.md).
The original files and both decoder profiles remain preserved. Capture setup and detailed
musical-state metadata still need documentation. Current validation passes 63 tests.
Reconstruction must use explicit preamble/boundary policy, preserve final symbols, pass
independent waveform tests at both rates, and undergo manual restore with behavioral checks
and re-capture. No pattern-offset inference is justified by this decoding alone.

## Session 3 update

Strict reconstruction passes at both supported rates and current validation passes 96 tests. The generated restore file and manual checklist are in [reconstruction notes](reconstruction.md). Hardware testing remains pending.

## Hardware rejection and waveform correction

Candidate 001 failed restoration while an original baseline restored through the same path. A corrected staggered-quadrature waveform and nominal 7812.5 Hz carrier now match independently recorded waveform windows substantially better. See [reconstruction notes](reconstruction.md). Software equality alone missed the original transition error.

## Local hardware acceptance

The user reports successful restoration of corrected candidate 002. The exact artifact is recorded as accepted in its manual restore record. Detailed musical verification and a post-restore capture comparison remain pending.

## Controlled hardware roundtrip validated

The user restored corrected candidate 002 and immediately backed up without intervening
state changes. The lower-level re-capture matches all 1,970,367 labels per channel and
their exact counts against baseline 002/003, with zero alignment or discarded labels.
See [controlled re-capture validation](../experiments/reconstructed-002/validation.md).
This is evidence for this local device/state/playback path; it does not verify arbitrary
state editing or every encoder input. The current recording level is suitable when using
the explicit 0.0063 threshold profile.
