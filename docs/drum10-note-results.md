# Sound10/key1 drum note is localized

The physical addition at Pattern1/Step1 passes every preservation check with543 valid
native packet checksums. Normal sign-crossing decode at threshold0.0063 succeeds.
Only Pattern1 packets4/7 change, with bytes27/28/29 becoming **0df883** and auxiliary
byte777 becoming **10** hex (16 decimal). This independently maps Sound10 to cell10
in the observed pattern row. The existing Sound3 note on Step1 is intact.

The sound-cell mapping, packet-location and Sound3-primary-equality predictions pass.
The melodic auxiliary **F0** prediction fails: the measured value is **10**. The
alternative Sound2-primary **0d2831** comparison also fails. Original predictions and
results remain unchanged; the writer uses the observed drum pair and never substitutes
the failed melodic value. No meaning is assigned to the auxiliary upper nibble or to
unobserved drum-key values.

Every other note/step, all15 other patterns, all sound/reference packets and sample
codes, footer and every other plain packet remain identical. The user reports "done"
for the registered physical control; pattern playback was not requested before saving.

- [Saved predictions](../experiments/drum10-note-predictions-001.json)
- [Measured results](../experiments/drum10-note-results-001.json)
- Capture: `experiments/event-020-b-drum10-key1-step1/capture.wav`
- Capture SHA-256: `17cc220dfa4c97f06606ad3c131be8f2bc6080fe7a12fc8be27842ca5c118817`
- Artifact SHA-256: `7626a958c17a3d8914f5b90bc9a17fccad263e3ce5a5e2ef40449c5108b68ad0`
- Body SHA-256: `edd7c74f1817ee7bf0afb6b3c7cb9340beed04f8a2da813e4b662b2ba5ff02c7`

The read-only export is **experiments/exported-drum10-note-001/project.json**. The
exact Sound10 primary0df883/auxiliary10 pair receives `calibrated_drum_slice_key: 1`,
separate from melodic `calibrated_keyboard_key`. Unknown drum pairs retain raw values
with no slice-key projection. Existing melodic/drum previews and all source packets
are retained. Export reports remain software-only.

The experimental `clone_drum_cell` and `remove_drum_cell` operations support only this
opaque Sound10/key1 note in Pattern1 and the accepted Sound10 start4045/end6045 copy
context. Source/target rows permit only calibrated Sound2/Sound3 neighbors. Empty targets,
matching primary/auxiliary cells and exact known parameters are required. Unknown notes,
occupied destinations, other sounds/patterns/keys or sample contexts are rejected.

Removal of the genuine added note reproduces the entire before-addition baseline.
Copying to Step9, removing Step1, copying back from Step9 to Step1 and removing Step9
reproduces the complete genuine addition body. Removing both copied notes reproduces
the complete earlier baseline. Opaque global packets and all neighboring notes remain
intact. These are software reconstruction checks, not a generated device test.

The first candidate adds only the Sound10 cell at Step9 alongside existing Sound2 and
Sound3 notes. It passes strict waveform/whole-body checks and its inverse reproduces
the source. It awaits a separate [restore and recapture](native-drum-cell-copy-restore-test.md).
General drum key encoding, note parameters and arbitrary polyphony remain unresolved.
