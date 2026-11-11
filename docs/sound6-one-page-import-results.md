# The one-page ordinary WAV import restores exactly

The user confirmed restoration, the new higher short Sound6 beep, silent Sound7 and
unchanged Sound4/Sound5/Pattern1 checks. The capture passes 832 native checksums using
the normal 0.0063 acquisition and matches the entire generated target body/packets.

Sound6 retains exactly 4,096 code bytes and header `000000002809000005`
(start 0/end 2,344/owner 5). Every supplied sample code and all 1,752 zero tail codes survive.
The imported 2,344-code window is exact, no larger buffer appears, and all non-Sound6
plain packets/patterns remain unchanged. This confirms a one-page serialized buffer
and an endpoint that is not aligned to the recording-length values seen earlier.

The actual saved 100 ms 48 kHz stereo PCM file was resampled 125/256 and mu-law encoded
without gain normalization. Its independently decoded preview fits 1,200 Hz; the user
confirmed the short audible beep. Serialized capacity/window acceptance does not
measure physical RAM units, prove smaller minimum lengths or establish every import
combination. The compiler report remains software-only; acceptance is separate.

- [Exact recapture comparison](../experiments/edited-sound6-one-page-import-001/hardware-recapture-results-001.json)
- [Hardware acceptance](../experiments/edited-sound6-one-page-import-001/hardware-acceptance-001.json)
- [User observation](../experiments/edited-sound6-one-page-import-001/manual-observation.json)
- Current read-only export: `experiments/exported-one-page-sound6-import-001/project.json`
- Capture SHA-256: `1c879e3bc19ff8948feb9692d0e05548ad7ad0251577854e3f590857ae3b0c7b`
- Artifact SHA-256: `9e3b970249348f4a8b6775c66e5aa3e359c5100b22200e72403fced7ca650af9`
- Native body SHA-256: `c9ddfcbea8921fef3d62e06959e378a0fa20cf5351c59ba089cfe40974780b66`

Seven melodic/three calibrated drum previews and all 32 export content hashes pass.
The public [bounded WAV-import command](sample-import.md) reproduces this accepted
restore WAV byte-for-byte. The next [mono 44.1 kHz import](sound6-mono-WAV-import-control.md)
uses that command to import a longer rising pitch sweep.
