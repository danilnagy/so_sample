# Restore a Sound6 sample with nine serialized data pages

The next backup is **experiments/edited-sound6-nine-pages-001/restore.wav**.
It creates Sound6 from the earlier hardware-tested500Hz sample, retaining the complete
original32768-code buffer/header and appending exactly4096 zero codes as one extra page.
The new capacity is36864 codes: nine4096-code pages, not divisible by8192.

The logical window stays0/30912/owner5, so the same lower tone should last about1.3seconds.
The total zero tail becomes5952 codes. Sound7 remains empty, every previous sound and
pattern is unchanged, and total backing capacity is167936 codes, below the earlier
observed172032-code state. All WAV/phase/native roundtrip checks pass in software.

1. Restore the complete **restore.wav** above through the proven stereo receive path
   at the established playback level: **write + sound + record** to receive.
2. Select **Pattern1 / Sound8 / TONE**, stopped/write off. Leave both knobs and all
   other settings unchanged.
3. **Before audition or pattern playback**, save a complete stereo backup at the
   successful reduced levels as **experiments/edited-sound6-nine-pages-001/capture.wav**,
   including a second of trailing silence.
4. After saving, check **Sound6/key1** plays the familiar lower tone for about1.3seconds,
   **Sound7/key1** remains silent, and Sound4/key1, Sound5/key1 and Pattern1 sound
   unchanged. Return to Sound8/TONE stopped/write off and report restore acceptance
   and the checks, including any difference.

The registration pins the current empty baseline, original sample template and entire
generated target before hardware testing. Core checks require a valid changed capture
with a populated Sound6 and preserved patterns/selectors. Capacity36864, rounding to
40960, dropping the extra unused page to32768 and any other observed capacity are
reported separately. Header/original32768-code prefix, entire supplied36864-code prefix,
logical window and unrelated packets are independent preservation checks.

A rounded or truncated buffer is not mislabeled as an exact restore. Unknown owners
or layouts are reported without guessing samples, and expected target bytes never
guide acquisition or native checksums. Matching nine serialized pages would establish
that representation's acceptance; it would not identify physical RAM allocation units
or establish a universal capacity-selection rule with the endpoint held fixed.

- [Software validation](../experiments/edited-sound6-nine-pages-001/software-validation.json)
- [Restore registration](../experiments/edited-sound6-nine-pages-001/restore-registration.json)
- Preview only: `experiments/edited-sound6-nine-pages-001/sound6-preview.wav`
- Generator: `python -m scripts.make_odd_page_sound6_candidate --out-dir <fresh-directory>`
- After normal capture decoding: `python -m scripts.check_odd_page_sound6_restore`
- Expected geometry:968 packets/end194396
- Restore WAV SHA-256: `a0fb91b9e48580b8d57fc23acd3935a1463a9807411369501ccce2bd6a06ae36`
- Target body SHA-256: `196444b1b49e0826e9ce7f4b0a4672af4e0a19a7b728a9618408a12e1ee3b3a7`

This is an isolated pending capacity experiment; public copy/deletion operations retain
their32768-code context guards and no general allocator is enabled.

The device now retains the exact nine-page capacity and entire generated body, with
audible checks confirmed. See [results](sound6-nine-page-results.md). The next test is
an [ordinary WAV import into one page](sound6-one-page-import-control.md).
