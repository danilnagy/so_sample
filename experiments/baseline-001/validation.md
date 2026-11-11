# Baseline 001: initial validation

Original file: capture.wav. SHA-256:
6312a96c924ff3414b51584a1e86a2a950860b168d03cab9d735b2ed1d370370

- 44,100 Hz, signed 16-bit PCM, two independent recorded channels.
- 11,316,060 frames; 256.6 seconds.
- Left/right peaks approximately 0.534 / 0.509; no near-full-scale samples.
- Channel correlation approximately 0.000164; channels are not duplicates.
- User reports successful restoration of this original capture to their PO-33.
  Detailed state checks and a post-restore re-capture have not been supplied.
- Original SHA-256 verified unchanged after analysis; reference scripts used a copy.

The upstream converter at dc7c950470b348b65fbad0cfcfe100a1a89f90a9 was run twice
unchanged using Python 3.12.15. Both returned exit 0 and produced identical 1,002,234-byte
outputs with SHA-256 027a504ff33b61e6333cc06232d2c402f5e5c214a32316f3f32173ecbfd8c92a.
Commands, logs, the source copy, binaries and strict comparison are under
 derived/reference-001/ (ignored in Git).

This establishes deterministic upstream output for this recording, not verified transport
payload or a lossless decoder. The upstream's incomplete-group and shorter-channel
truncation remain unresolved. Its 50000-unit signal-acquisition threshold was never met by
this 16-bit recording, so it processed from sample zero instead of reporting acquisition.
No generated waveform or generated-file hardware restoration has been validated.

The genuine capture inspection regression test passed against the pinned hash, header
frame count, rate, subtype and channel count. Capture setup, any processing applied,
and the device's musical state remain unknown until documented by the user.

Next: preserve separate channel symbols and partial groups in versioned artifacts; measure
synchronization uncertainty and discarded boundaries before reconstructing transfer audio.
Repeated unchanged recordings will then help distinguish decoder instability from state changes.
