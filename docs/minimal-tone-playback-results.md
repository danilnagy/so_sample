# Retained-tone playback measured

The supplied ordinary playback recording is a single, steady tone with no clipping.
The original5.95-second stereo44.1kHz PCM16 WAV is retained as
../experiments/empty-001-h-sound3-copy-return/sample-playback.wav, SHA-256
`0ab0c5b150bc6c32b70f4f78705b6c7797a6d4835077786197dbae322ebef047`.
The user confirmed completion of the Sound3/key1 protocol; exact actions were not
independently observed.

Both channels contain1.25s of audible tone at approximately561.954Hz, with10ms boundary
resolution. A single sine explains99.69% of interior variance. Relative to the375Hz source,
the ratio1.49854 is approximately+7.003 semitones, consistent with note/pitch transposition.
This is audible playback duration, not the native buffer length. The earlier old-state
playback remains a separate source.

Packet decoding subsequently exposes a65536-byte backing buffer and a Sound3 counter64704.
The signed-complement mu-law/nominal23437.5Hz interpretation recovers375.015Hz and1.87s
audible tone from that buffer, with99.97% single-sine fit. The decoded example WAV is
../experiments/empty-001-h-sound3-copy-return/derived/packet-001/decoded-sound3.wav.
The nominal full counter covers about2.76s, including quiet audio; it is not the audible
tone span. Source button timing, exact ADC rate and inclusive endpoint semantics remain
unverified. See packet-decoding.md and sample-codec-calibration-001.json for the evidence.

This completes the requested playback observation. The next hardware step tests the
new generated Sound3 trim edit, per native-trim-restore-test.md.
