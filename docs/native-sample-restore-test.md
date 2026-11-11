# First sample replacement: hardware validated

The user replied done to the requested restore, listening and recapture protocol. The
new backup matches the generated native body and every backing sample code exactly,
with all **511** checksums valid. All sound headers and trim counters are unchanged,
and differences from the preceding backup are restricted to owner sample-data packets.
See [hardware validation](../experiments/edited-sample-001/hardware-validation.json).
The recording is unclipped and the independent amplitude-clock check has no interior
quarter-sign disagreements. Exact acoustic pitch/duration observations were not supplied.

The following instructions are retained as the completed test protocol.

The prior Sound3 trim edit is now hardware validated, including an exact native packet
body match from its recapture. This next test changes the **sample audio** while keeping
the existing buffer size, all trim headers and the empty pattern state.

Restore **experiments/generated-sample-750-001/restore-750hz.wav** with the same stereo
playback path and levels that just worked. It is 44.1 kHz PCM16, about 23.1 seconds. Play
the complete file after entering receive mode with **write + sound + record**.

1. Report whether restore completes successfully.
2. With write off and the sequencer stopped, select **Sound8** and tap **key1** once.
   The tone should be an octave higher than before and remain long, roughly 1.3 seconds.
3. Select **Sound3** and tap **key1** once. It should have the same higher pitch and
   remain brief, roughly 0.23 seconds. Sounds 1/2/3/8 all share this replaced buffer.
4. Reselect **Sound8**. Keep TONE, empty Pattern1, write off, stopped playback and
   the same recording level. Capture a full stereo backup as
   **experiments/edited-sample-001/capture.wav**.

The imported source is a 750 Hz, two-second tone at nominal sample rate 23437.5 Hz after
conversion. Key1 playback was previously measured above the source pitch, so expect
roughly 1124 Hz from the device; the useful listening check is the octave increase.
The long tone has a slightly different duration because the previous physical recording
retained about 1.87 seconds of audible source. Sound3's counter is unchanged at 8000.

Use **restore-750hz.wav** for the restore. The neighboring **sample-750hz.wav** and
**imported-preview.wav** are ordinary audio previews, not backup transfers. No automatic
playback has been performed.

Software validation confirms all 511 checksums, strict full-phase/count waveform
roundtrip, unchanged packet sizes, unchanged sound headers and changes restricted to
owner sample-data packets. It is recorded in
[software validation](../experiments/generated-sample-750-001/software-validation.json).
At candidate preparation the full suite passed 181 tests, including the genuine trim recapture, sample-code
levels, invalid inputs, quantization bounds and preservation of unrelated packet data.
The current suite, including the genuine sample recapture and raw pattern reader, passes
244 tests. Ruff lint and formatting checks pass for all 89 Python files.
Expected encoded body SHA-256:
`8f851166868fd99e7935a5942a2b82181f0268c3a05303f08852a0f06ebb30a0`.

The prior verified backup remains
**experiments/edited-trim-001/capture.wav**. The
[official guide](https://teenage.engineering/guides/po-33/en) documents receive mode
and that restore replaces device samples and patterns.

Reproduce this candidate from the saved verified state:

```powershell
.\.venv\Scripts\python.exe scripts/make_sample_candidate.py experiments/edited-trim-001/derived/analysis-001/capture.symbols.npz --out-dir experiments/generated-sample-750-002
```

This writer supports a fixed-size existing melodic buffer only. Allocation, resizing,
nonzero trim starts and separate audio for the copied sounds require further work.
The next control is [one melodic pattern note](melodic-step1-control.md).
