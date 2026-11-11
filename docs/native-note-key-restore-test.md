# Generated note-key edit: hardware validated

The user explicitly confirms alternating pitches work, and the supplied backup's full
native body matches the generated target exactly, with511 valid checksums and unchanged
samples and other note parameters. See
[hardware validation](../experiments/edited-note-key-001/hardware-validation.json).

The initial crossing decoder encountered a left timing slip and failed a packet checksum.
The separate measured-clock method recovers the full exact frame using waveform signs
and pre-frame-only alignment, without target data or packet repair. Both the initial
failed artifact and recovered artifact remain saved; see [recovery notes](measured-clock-recovery.md).
Capture timing relative to playback was not explicitly reported. The original planned
test below is retained for provenance. The next control is [keyboard key16](melodic-key16-control.md).

Restore **experiments/generated-note-key-001/restore-alternating-keys.wav** with the
same stereo playback path and levels that worked previously. It is44.1kHz PCM16,
approximately23.1seconds. Enter receive mode with **write + sound + record** and play
the complete transfer once.

This candidate changes only Sound3's **Step13** from key1 to key2. The physically edited
Step5 already uses key2. Pattern1 should have **four evenly spaced short tones with
alternating pitches**:

| Step | Keyboard key |
| ---: | ---: |
| 1 | 1 |
| 5 | 2 |
| 9 | 1 |
| 13 | 2 |

1. Report whether restore completes successfully.
2. **Before playing the pattern**, keep Pattern1, Sound8 selected, TONE, write off,
   playback stopped and the same recording settings. Save a full stereo backup as
   **experiments/edited-note-key-001/capture.wav**.
3. After saving it, play **Pattern1** for one or two loops. Report whether four short
   tones alternate between the two pitches, then stop playback. Leave this pattern
   in place afterward.

If capture must be recorded after playback, explicitly report that timing; the previous
four-note after-playback backup matched exactly, but this next result still needs its
own comparison. The prior physical key2 backup is preserved at
**experiments/event-008-b-melodic-key2/capture.wav**.
Controls follow the [official PO-33 guide](https://teenage.engineering/guides/po-33/en).

The candidate changes exactly one Pattern1 payload byte, offset962 F0→F1, in plain
packet7. Primary note data and the upper auxiliary nibble are unchanged. Every sample,
other note field and other pattern is preserved. The writer reproduces the genuine
key2 control and its inverse exactly. It is limited to the locally observed Sound3
keys1/2 and known primary/auxiliary values; other note keys are rejected.

- [Software validation](../experiments/generated-note-key-001/software-validation.json)
- WAV SHA-256: `825c68b6bcb087e147f9d9cde873a368e09540368b15741f020052170db963d0`
- Expected native body SHA-256: `91b37d61e3bc71de72748dfd846892e62a7d839a9332f13a6f9c56687cdeadf0`
- Exactly511 packets, frame end89396; strict phase/count roundtrip and exact target packet
  recovery from the generated waveform pass. Hardware acceptance and exact recapture of
  this key1/2 edit now pass as described above.

The full suite passes **244 tests in69.17s**. It includes genuine-WAV forward/inverse key
reproduction, single-byte preservation at multiple step positions, unsupported-input
rejection, existing step cloning after the shared pattern-write refactor and CLI source
protection. Ruff lint and formatting checks pass for all89 Python files.

Reproduce the candidate in a fresh output directory:

```powershell
.\.venv\Scripts\python.exe scripts/make_key_candidate.py experiments/event-008-b-melodic-key2/derived/analysis-001/capture.symbols.npz --out-dir experiments/generated-note-key-002
```

The reusable CLI produces a phase artifact and report without playing it:

```powershell
.\.venv\Scripts\python.exe -m po33_re set-note-key experiments/event-008-b-melodic-key2/derived/analysis-001/capture.symbols.npz --pattern 1 --step 13 --sound 3 --key 2 --out keyed.symbols.npz --report keyed.report.json
```
