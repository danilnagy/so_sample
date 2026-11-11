# Mono WAV import matches the hardware recapture exactly

The public `import-sample` command successfully restored the saved mono PCM16
44.1 kHz rising pitch sweep into unshared Sound6. The user reported **done and confirmed**
in response to the restore and audition checks: the approximately 0.75-second sweep,
silent Sound7 and unchanged Sound4, Sound5 and Pattern1.

All 951 native packet checksums pass. The complete recapture equals the generated
native body, including all 17,579 imported codes, the 15,189 zero tail codes and every
unrelated packet. The 32,768-code buffer and header `00000000ab44000005`
(start 0 / endpoint 17,579 / owner 5) remain exact. The new endpoint is preserved
without rounding to an earlier physical recording-length boundary.

The source file contains 33,075 frames. Resampling 625/1176 yields 17,579 native
frames without gain normalization. The compiler report remains software-only;
hardware acceptance is recorded separately for this exact source and device state.
Other lengths, slot pairs, shared-owner replacement and general memory limits remain
outside this evidence.

The accepted artifact is `derived/analysis-002/capture.symbols.npz`, decoded using the
established threshold 0.0063. The initial CLI-default threshold 0.00030517578125
attempt in `analysis-001` fails the first native packet checksum and is retained.
No packet prediction, symbol repair or expected sample data guided acquisition.
Capture peaks are about 0.165 and 0.159, with no clipped frames.

- [Native recapture checks](../experiments/edited-sound6-mono-WAV-import-001/hardware-recapture-results-001.json)
- [Separate hardware acceptance](../experiments/edited-sound6-mono-WAV-import-001/hardware-acceptance-001.json)
- [User observation](../experiments/edited-sound6-mono-WAV-import-001/manual-observation.json)
- Current read-only project: `experiments/exported-mono-WAV-sound6-import-001/project.json`
- Capture SHA-256: `ea299978cae355585815d8677d4835f514209a41c2cc36b3f2976b7a5dc1287c`
- Artifact SHA-256: `42abc578dd9829432de80f03f8c2ac9dd9bb5725cca964ba928b7e337c69ae44`
- Native body SHA-256: `5b557a2586907b90705bed847b63e33745d0cef85bc27e06f80e6f0601f29b7c`

All 32 exported content hashes pass. Tests independently reproduce the genuine
native body from the saved PCM input, both replacing the prior short sample and
reimporting into the current state. The next [copy test](imported-sound6-to7-copy-control.md)
checks reference copying with this imported endpoint; public copy/deletion guards
retain their earlier scope until suitable evidence is available.
