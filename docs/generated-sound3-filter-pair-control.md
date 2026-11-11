# Generated fixed-16/52 FILTER restore controls

Both research targets start from the genuine exact center return. They change only
second-primary high-four and third-primary low-two bits in all 16 Sound 3 /
Pattern 1 cells, preserving pitch 14, volume 36 and every unrelated bit. Raw 16
reproduces the entire independent recorded low-pass interior body; raw 52
reproduces the entire independent high-pass interior body. These known physical
targets were already observed. The new registration freezes generated WAVs and
predicts their complete recaptures before restore testing.

Both WAVs use the established 44.1 kHz stereo PCM16 encoding at amplitude 0.5.
Software phase roundtrip and complete body/packet recovery pass. Generation does
not constitute hardware acceptance. The research constructor accepts only fixed
16/52 from the exact center body; public pitch and volume guards are unchanged.

## Next action: low-pass 16 only

1. Restore `experiments/edited-sound3-filter16-lowpass-001/restore.wav` using the
   established stereo restore path and playback level. Keep both knobs and audio
   settings unchanged.
2. Before ordinary playback, save a full backup as
   `experiments/edited-sound3-filter16-lowpass-001/capture.wav` at the established
   reduced recording level, with one second trailing silence.
3. Select Pattern 1 / Sound 3 / FILTER without turning either knob. Play the
   pattern, report whether restore succeeded and whether low-pass filtering is
   audible, then stop and ensure write is off.

No WRITE-held pass or separate `playback.wav` is needed. Report uncertainty or
unexpected behavior without adjusting the knobs to force the expected result.
The predicted entire recapture is
`b5e315b3f0703190ad42652eb57616385e52b2c92df04e3aa2bc1b936c005c37`.

## Later high-pass 52, after low-pass is verified

The prepared second file is
`experiments/edited-sound3-filter52-highpass-001/restore.wav`. Its full target is
`fd5c085eae8bcea16f167c240d014f770e588c0a205c1117c732021afa0102af`.
Wait for verified low-pass reception plus user listening evidence before requesting
this restore. It will use the same backup-before-playback and listening sequence,
with capture saved in its own folder. The high-pass checker requires a separate
verified first-leg hardware observation bound to this registration.

No quantitative amplitude response, Hz curve, numeric display value or complete
all-code law is predicted. The independent physical targets and observations are
hash-pinned. A matching field value cannot rescue any other changed byte.

- [Preregistration and frozen WAV identities](../experiments/sound3-generated-filter16-52-registration-001.json)
- [Low-pass software validation](../experiments/edited-sound3-filter16-lowpass-001/software-validation.json)
- [High-pass software validation](../experiments/edited-sound3-filter52-highpass-001/software-validation.json)
- [Independent interior results](sound3-filter-A-interior-results.md)
- [Research constructor](../scripts/prepare_generated_sound3_filter_pair.py)
- [Reception checker](../scripts/check_generated_sound3_filter_restore.py)

After independent threshold-0.0063 decoding, run
`python -m scripts.check_generated_sound3_filter_restore --leg lowpass`.
The later second leg uses `--leg highpass`. Reports are immutable and remain
hardware-unverified; listening and hardware evidence are separate. All 88 affected
checks pass, with production code unchanged since the last full 917-test run.

## Low-pass completed; high-pass is now the next action

Generated16 recaptures as the entire preregistered target and every packet, with
all unrelated state exact. The user confirms audible low-pass filtering. See
[results](generated-sound3-filter16-results.md). Original registration, generated
targets and software reports remain unchanged.

1. Restore `experiments/edited-sound3-filter52-highpass-001/restore.wav` using the
   established stereo path and playback level, without moving either knob.
2. Before ordinary pattern playback, save the complete backup as
   `experiments/edited-sound3-filter52-highpass-001/capture.wav` at the established
   reduced level with one second trailing silence.
3. Select Pattern 1 / Sound 3 / FILTER without knob movement, play with write off,
   report whether restore succeeded and whether high-pass filtering is audible,
   then stop.

No WRITE-held pass or separate playback recording is required. Keep audio settings
unchanged and report any uncertainty without adjusting the knobs to force a result.
The whole-body target remains `fd5c085eae8bcea16f167c240d014f770e588c0a205c1117c732021afa0102af`.

## Both legs completed

High-pass52 now recaptures as the entire independent target and every packet,
preserving pitch14/volume36 and all unrelated state. The user confirms high-pass
filtering. See [pair results](generated-sound3-filter-pair-results.md),
[bounded public operation](sound3-filter-edits.md) and the
[next public-plan center return](generated-sound3-filter-center-control.md).
