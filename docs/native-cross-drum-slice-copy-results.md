# Generated nonzero-start cross-drum copy accepted

The recapture matches the complete registered target with543 valid native checksums.
Normal sign-crossing decode at threshold0.0063 succeeds without recovery. The user
reports **"done and confirmed"** for restore, the Sound10/key1 short tone/source-key2
comparison and unchanged Sound9/keys1/2. These observations are recorded separately
from native-state validation; exact rendering duration and endpoint inclusivity remain
unmeasured.

Only packet415/selector24 changes from the physical-copy source. Sound10/key1 receives
the exact Sound9/key2 reference **cd0f00009d17000000**, start4045/end6045/owner0. Payload
offsets0/1/4/5 change. Both Sound9 references, the other15 Sound10 records, all65536
backing codes and owner header, melodic sounds, all16 patterns and every other plain
packet remain identical. No new packet, buffer or allocation is introduced.

- [Registered target](../experiments/edited-drum-slice-copy-001/restore-registration.json)
- [Hardware validation](../experiments/edited-drum-slice-copy-001/hardware-validation.json)
- [User observations](../experiments/edited-drum-slice-copy-001/audition-observation.json)
- Capture: `experiments/edited-drum-slice-copy-001/capture.wav`
- Capture SHA-256: `ac23213297cb3a1d0b56515bbb78bb5485b72cf5e420376ea591ae11f0d647cc`
- Artifact SHA-256: `c349b9e04482c881db859ec99352382643ae1538cd51b120a708aab390f1ae9c`
- Exact native body: `846092c09285da128689493f2a332fef8e0c22ac93fb710f9e0b994661fe971e`

The recording is stereo PCM16/44100Hz with left/right peaks0.1685/0.1614 and no clipping
indicators. These reduced levels remain suitable. The source capture, original target
registration, generated artifact and software reports remain unchanged. The hardware
report records this accepted device result; software/compiler reports remain
`hardware_verified: false`.

Explicit **--calibrated-drum-slices** project export can now include Sound10/key1 at
the two accepted copied windows: zero-start[0:2000] or nonzero[4045:6045]. It retains
the shared local-copy guards, source Sound9 contexts, owner0/65536 codes and literal
other15 Sound10 references. Unaccepted endpoints, starts, owners, keys or neighboring
records prevent this preview. The preview is unpitched/unscaled raw-code extraction
under the explicit half-open policy, not a Tone/filter simulation.

The current export is **experiments/exported-verified-cross-drum-copy-001/project.json**,
with four melodic previews, Sound9/keys1/2 and Sound10/key1, all16 patterns and every
raw/source packet preserved. **samples/10-slice-01.wav** is byte-identical to
**samples/09-slice-02.wav**, reusing the same encoded preview for the same raw window.
It contains4096FLOAT frames at48kHz. Other15 Sound10 keyboard positions remain
unverified and receive no previews. Default exports still include no drum audio.

The bounded copy writer keeps its existing scope: Sound9/keys1 or2 into existing
Sound10/key1. This accepts the tested nonzero-start key2 transfer; arbitrary combinations,
allocation, other drum mappings and destination endpoint editing remain unsupported.
The next [physical drum-note control](drum10-note-control.md) tests Pattern1/Step1
without changing any sample or reference.
