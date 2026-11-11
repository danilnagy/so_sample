# Physical cross-drum slice copy verified

The Sound9/key1 to Sound10/key1 capture passes all registered preservation checks and
all three separate predictions. The normal sign-crossing decoder at threshold0.0063
recovers543 packets with valid native checksums; no recovery or repair was needed.

Only packet415 under selector24 changes: `00000000cc0f000000` becomes
`00000000d007000000`, exactly the source Sound9/key1 reference. Its start0, endpoint2000
and owner0 are retained verbatim. Only payload offsets4/5 differ. This independently
maps Sound10/key1 to selector24; the other15 Sound10 key mappings remain unverified.

Both Sound9 references, all backing codes and their owner header, the other15 Sound10
records, all melodic sounds, all16 patterns and every other plain packet remain identical.
No allocation or packet resizing occurs. The native body is
`953e800ddd7d7e548515cec84b62491cb8cbae1d61579f9b643a08802c5b8f7d`.

- [Original predictions](../experiments/cross-drum-slice-copy-predictions-001.json)
- [Measured results](../experiments/cross-drum-slice-copy-results-001.json)
- Capture: `experiments/event-019-b-copy-drum9-key1-to-drum10-key1/capture.wav`
- Capture SHA-256: `9b2e9d4400a521063629dcf73d1de74972b7deb1a8b956d67f76c0787cf4be1b`
- Artifact SHA-256: `ada11958edae1e16d526c23e52db943c560244cf753ca4f3dcdc91e469bf4ca5`

The capture is stereo PCM16/44100Hz. Left/right peaks0.169/0.162 match the successful
reduced-level recordings; no clipping indicators are present. These settings remain
suitable for the next recording. The user reports "done" for the registered physical copy;
an acoustic comparison was not requested before saving and is not inferred.

The experimental `copy_drum_slice` plan operation permits only existing Sound9/keys1
or2 into Sound10/key1, copying the complete9-byte reference. It retains the observed
fixed-start source intervals, single-packet layouts, owner0/65536-code backing and literal
other14 Sound9/other15 Sound10 references. It allocates no data. The writer reproduces
the entire physical-copy body. Its inverse uses bounded source edits to copy the old4044
reference back, then restores source endpoint2000, reproducing the entire prior baseline.

The current read-only export is **experiments/exported-cross-drum-copy-002/project.json**.
Sound10/key1 carries `observed_key1_slice_copy_control`; only existing Sound9/keys1/2
receive audio previews. All raw packets/source files and exported content hashes are
retained. Export reports remain software-only.

The next candidate copies the already accepted nonzero-start Sound9/key2 reference
`cd0f00009d17000000` into Sound10/key1. Strict waveform/whole-body checks and the
candidate inverse pass. It needs a separate [restore and recapture](native-cross-drum-slice-copy-restore-test.md).
Arbitrary slots/keys, sample allocation, destination endpoint editing, Tone/filter
rendering and exact endpoint inclusivity are not established by this physical copy.
