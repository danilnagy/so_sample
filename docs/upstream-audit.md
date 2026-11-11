# Upstream audit (2026-10-07)

Static review against local checkouts. No upstream implementation has been copied into
our package. No upstream script has been run on the user's first recording yet.

| Repository | Pinned commit | License findings |
| --- | --- | --- |
| https://github.com/sZXZ/po33-experements | dc7c950470b348b65fbad0cfcfe100a1a89f90a9 | No project LICENSE/COPYING found in checkout. Do not copy its implementation without establishing permission. |
| https://github.com/cspotcode/PO-33-KO-backup-re | 4ed1475bc04faa266ef0b534ef87aa2a4358ac2d | No project license found; package.json has no license field. Vendor SoX GPL file applies to that component, not automatically the repository's own source. |

## Python converter

- Reads 8-bit unsigned PCM with subtraction of 128, signed 16/24-bit PCM, and a fallback
  signed 32-bit branch. Integer thresholds are not normalized across widths.
- Signal acquisition threshold is 50000: unreachable in signed 16-bit audio. If no sample
  exceeds it, start remains zero; conversion can still continue rather than fail.
- Zero-crossing threshold is 10 raw units. Silence/noise and rate drift require diagnosis.
- Uses nominal 7800 Hz carrier and quarter-cycle sign intervals; phase synchronization
  finds the first `11`, reinserts one bit, and inspects pairs at four-interval strides.
  This is an absolute waveform phase label, not verified decoded protocol bits.
- Phase labels map A=3, B=2, C=0, D=1; four values pack least-significant pair first.
- Incomplete final four-symbol groups are dropped. No original symbol count is recorded.
- Mono input is duplicated. More than two channels use only the first two.
- Packed channel bytes are interleaved only up to the shorter channel; the tail is lost.
- Missing synchronization returns an empty sequence; file creation alone can still succeed.

## Python reconstitutor

- Defaults to 48000 Hz, signed 16-bit stereo and amplitude 28000.
- Odd interleaved byte counts invent a zero-valued right byte.
- Adds two seconds of A carrier on both channels, regardless of captured prefix content.
- Crossfades current and next oscillator phases during the latter part of the cycle.
- Iteration stops at `max_len - 1`; the final phase is used as lookahead but has no complete
  own cycle. Unequal channels are filled with A. Validate endpoints before porting.
- Success means a WAV was written; there is no hardware acceptance or payload validation.

## TypeScript reference

Reviewed README, package.json, src/core.ts and src/cmds/parse.ts.
The parser takes separate signed 8-bit raw channel files, with a threshold of 10,
interpolated crossings, 7800*4 sign intervals per second, first-11 acquisition, and
A/B/C/D phase labels. Raw channel generation reads signed bytes.
Its uncertainty calculation divides the rounding residual by samplesPerBit again;
calibrate diagnostics independently before adopting that metric. First crossings use
an explicit approximation. The README's internal sample encoding and rate remain leads.
Other recording/playback commands have not been executed or fully audited.

## Next evidence needed

Run the documented Python scripts with explicit argument lists on copies of a registered
capture, saving logs, command arguments, interpreter version, output hashes, and source
hashes under derived/. Compare each channel's exact counts before any packing/truncation.
These checkouts contain upstream data; none is registered as a reviewed genuine regression
fixture for this project. Do not treat third-party recordings as local hardware validation.

## Local baseline run

The Python converter was subsequently run twice unchanged against a copy of baseline-001.
See [baseline validation](../experiments/baseline-001/validation.md) for hashes, results
and limitations. Both outputs are identical, but lossless decoding is not established.
The original capture restored successfully according to the user; no reconstructed
waveform has been restored.

## Reconstruction audit update

Additional review of cspotcode src/cmds/replay-backup.ts confirms the whole-phase linear
crossfade from 0.6 to 0.9 cycle and explicit broken-file-output warning (the file path
adds an unsigned bias to a 16-bit WAV stream). This project's own PCM WAV writer does
not use that path. The first independently written blend encoder failed hardware restoration
even though both decoders agreed on labels. Actual capture waveform evidence supports
staggered quadrature updates and approximately 7812.5 Hz synthesis instead. See
[reconstruction notes](reconstruction.md) and the tracked waveform audit. Do not treat
reference decoder agreement as waveform fidelity or hardware acceptance.
