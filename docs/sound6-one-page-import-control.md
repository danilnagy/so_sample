# Restore an ordinary WAV import into a single-page Sound6 buffer

The next backup is **experiments/edited-sound6-one-page-import-001/restore.wav**.
It replaces Sound6's nine-page buffer with one4096-code page and imports the saved
ordinary source WAV **input-sample.wav**: a1200Hz100ms tone, identical stereo PCM16
at48kHz, requested peak0.25 and5ms fades.

The input is read from the saved PCM file, resampled by125/256 to nominal23437.5Hz,
then quantized with the established signed-complement mu-law encoder. There is no
gain normalization.4800 input frames become2344 native frames; the one-page buffer
has1752 zero tail codes and header `000000002809000005` (start0/end2344/owner5).

The software preview independently fits1200.001Hz and an active span around0.1seconds.
Its fit uses60000 trailing zero frames for analysis only; the saved preview contains
4801 frames at48kHz. All input/sample-code, waveform, native-body and plain-packet
checks pass. The source WAV and original capture/artifact are preserved with hashes.
All other sounds/patterns are unchanged and Sound7 remains empty.

1. Restore the complete **restore.wav** above through the proven stereo receive path
   at the established playback level: **write + sound + record** to receive.
2. Select **Pattern1 / Sound8 / TONE**, stopped/write off. Leave both knobs and all
   other settings unchanged.
3. **Before audition or pattern playback**, save a complete stereo backup at the
   successful reduced levels as **experiments/edited-sound6-one-page-import-001/capture.wav**,
   including a second of trailing silence.
4. After saving, check **Sound6/key1** plays a new higher short beep, about0.1seconds.
   **Sound7/key1** should stay silent, and Sound4/key1, Sound5/key1 and Pattern1 should
   sound unchanged. Return to Sound8/TONE stopped/write off and report restore
   acceptance and all checks, including any difference.

The registration pins the actual input WAV, source, complete generated body and sample
record before testing. Core checks require a valid changed capture with populated
Sound6 and preserved selectors/patterns. Exact4096 capacity, larger capacity, the2344
endpoint, supplied code prefix, logical window and all unrelated packets are evaluated
separately. A changed endpoint with identical codes must not be reported as code loss;
a larger buffer with the same imported window must not be reported as exact restoration.

This control changes both serialized capacity and logical endpoint. Failure by itself
would not identify which change caused it. The importer is currently a restricted
research utility for100ms48k identical-stereo PCM; no arbitrary WAV-import API or
public allocation/copy/deletion scope is enabled by this pending test.

- [Software validation](../experiments/edited-sound6-one-page-import-001/software-validation.json)
- [Restore registration](../experiments/edited-sound6-one-page-import-001/restore-registration.json)
- [Ordinary source metadata](../experiments/calibration-one-page-import-001/source.json)
- Input sample copy: `experiments/edited-sound6-one-page-import-001/input-sample.wav`
- Preview only: `experiments/edited-sound6-one-page-import-001/sound6-preview.wav`
- Generator: `python -m scripts.make_one_page_sound6_import <100ms48k-stereo-PCM.wav> --out-dir <fresh-directory>`
- After normal capture decoding: `python -m scripts.check_one_page_sound6_import_restore`
- Expected geometry:832 packets/end160948
- Input WAV SHA-256: `9fb2d229628767c80485c9dd23b24072218c36f910413483b5a15d552298a288`
- Restore WAV SHA-256: `f8736ed60f4206b9b08ee2d1c209e6797f2c8bb955c33247b876d951e37f20eb`
- Target body SHA-256: `c9ddfcbea8921fef3d62e06959e378a0fa20cf5351c59ba089cfe40974780b66`

The capture now matches the complete target, exact4096 capacity and2344 endpoint,
with all audible checks confirmed. See [results](sound6-one-page-import-results.md).
The importer is now a [bounded CLI command](sample-import.md); the next device test
uses [mono44.1k audio](sound6-mono-WAV-import-control.md).
