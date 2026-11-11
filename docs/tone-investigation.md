# Partial-tone control, round 7

The approximately one-second retained tone was sufficient to produce a valid new backup
and useful transport observations. State/sample decoding remains unresolved. Storage
was not cleared, and no original recording was edited.

## Capture and waveform checks

The original is ../experiments/event-006-b-tone/capture.wav, hash
dfcd59dfa2ae04973f49090b0997e7f1508aaf62e18a9293362240ad397e54f7.
44100 Hz PCM16 stereo, 11783334 frames, 267.195782 seconds, peaks ~0.1688/0.1610,
no clipping. Source and derived artifact hashes are pinned in fixture/analysis reports.
The user estimates about one second stored, with full storage; exact duration is unknown.

At threshold 0.0063 the two label counts are 2070730/2070729, compared with
1970367/1970367 before sampling. Count increases 100363/100362 are transport values,
not decoded sample-byte counts or an independently verified duration. Both raw channels
first diverge at 829509. There is no invented fresh A; corrected event-005-b-joint is
the explicitly reused control.

The independent amplitude-derived clock agrees with existing labels and all four quarter
signs throughout the checked interior, as recorded in waveform-probes-007.json. This
again supports phase capture fidelity while leaving acquisition edges and payload unknown.

## Repetition and displaced suffix

Report ../experiments/tone-structure-001.json scans 16384-value windows at stride8192,
testing lags1-2048 with exact categorical equality fractions computed by one-hot FFT
correlation. The report retains top windows per view/channel/state. An approximate
correlation maximum does not itself establish an exact period.

Full-stream exact-run tests, excluding the acquisition prefix, find the following at
post-observation candidate lag520 in staggered phase increments:

| State/channel | Equal lag-pair span | Covered value span | Matching pairs |
| --- | --- | --- | --- |
| Before, left/right | [1164187,1164711) | [1164187,1165231) | 524 |
| Tone, left | [1179129,1181213) | [1179129,1181733) | 2084 |
| Tone, right | [1179125,1181213) | [1179125,1181733) | 2088 |

The common covered new region [1179129,1181733) has smallest exact period520 in both
channels. The new region is longer, but a shorter same-period region already existed.
It cannot be uniquely identified as the recorded tone or a codec feature from this result.

Diagnostic increments shifted by +100362 in the new recording match the old recording
exactly from old index1609433 to1970365, length360932, on both channels. Adjacent shifts
100356-100364 are also reported; their late matching fraction is near incidental equality,
while +100362 gives ~82.5% across the broader late window. The displacement was selected
after inspecting anchors/counts, not a preregistered prediction. Stored arrays are unchanged.
This verifies a shared displaced tail, not a global single-insertion model or sample offset.

520 increments could serialize to260 stereo bytes in one candidate layout. The count
increase is also near193*520, with extra boundary increments. These arithmetic coincidences
motivate a frame hypothesis, but do not prove payload256/checksum4 or any other framing.

## Checksum hypotheses and false hits

Report ../experiments/checksum-probes-001.json uses real consecutive data from a
post-observation region starting1179200, not an artificial repeated raw-phase ring.
It tests raw labels, staggered phase, modular phase increments and staggered coordinate
XOR; four packing offsets and every label permutation, with separate permutations for
each channel in the stereo model. First mapped label occupies low bits; channel bytes
interleave left/right. The tested candidate formats are:

- Per-channel128-byte body plus2-byte CRC16 with polynomial0x1021, initial0/FFFF,
  final XOR0/FFFF and either stored endian: 798720 comparisons.
- Stereo256-byte body plus4-byte Python zlib default CRC32, either stored endian:
  4792320 comparisons.

Checksum functions and parameters follow [Python binascii documentation](https://docs.python.org/3.12/library/binascii.html)
and [Python zlib documentation](https://docs.python.org/3.12/library/zlib.html). No claim
is made that the device uses these algorithms. Other polynomials, reflected CRC16,
different header coverage, symbol-level interleaving and reversed temporal pair order
are not tested here.

Seventeen CRC16 settings match a single candidate block. Each then fails all64 subsequent
holdout blocks, all with distinct body contents. No tested CRC32 setting matches. Thus
single-block coincidences were rejected rather than accepted as format evidence. These
results do not exclude all possible checksums, coding or encrypted validation fields.

## Next required observation

Actual retained sample content has not been measured: the estimate is about one second,
and available memory interrupted recording. Before attributing periodic transport to
that sound, record a few seconds of normal Sound8 playback, triggering melodic key1
once with sequencer stopped/write off. Save as
../experiments/event-006-b-tone/sample-playback.wav. Return to Sound9/slice1 afterward;
preserve current memory and patterns. No further full backup is requested for this control.

This lets us measure audible duration and frequency and assess recording/processing.
Melodic playback can transpose the input, and existing sample parameters can process it,
so its waveform is not presumed native stored PCM or exactly375 Hz.

## Reproduction

```powershell
.\.venv\Scripts\python.exe scripts/tone_structure.py experiments/event-005-b-joint/derived/analysis-002/capture.symbols.npz experiments/event-006-b-tone/derived/analysis-001/capture.symbols.npz --out experiments/tone-new.json
.\.venv\Scripts\python.exe scripts/checksum_probes.py experiments/event-006-b-tone/derived/analysis-001/capture.symbols.npz --out experiments/checksum-new.json
```

Independent tests compare FFT fractions with direct equality counts, exact period/run
boundaries, CRC searches on packets built using bit-by-bit reference implementations,
and corrupted holdouts. The genuine tone capture is separately pinned and checked for
its observed period. No writable sample or pattern field is inferred.

The complete regression suite passed: 144 tests in43.73 seconds. Ruff lint and formatting
pass for src/tests/scripts. The original tone-control WAV remains byte-identical to its
registered source hash. Memory state has not been reset or cleared.

## Playback control completed

The user supplied ordinary Sound8 playback, with one steady audible tone lasting1.26s
at about561.946 Hz. A single-sine model explains about99.93% of the interior variance,
with no clipping. Input was375 Hz: ratio1.498523 corresponds to+7.0025 semitones.
This is consistent with note/pitch transposition, but the actual pressed note and
parameter values remain unobserved. Played duration is not native stored duration;
the backup count difference cannot be converted into a sample-byte rate using it.
See ../experiments/event-006-b-tone/playback-analysis.json and validation.md.

This completes the requested single-sample control. The subsequent minimal-state series
is prepared in empty-baseline.md and ../experiments/empty-001-a plus empty-001-a-repeat.
Reset/deletion and new captures are manual user actions and have not been reported yet.
Existing captures retain their original state meaning; none is relabeled as empty.
