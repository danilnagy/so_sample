# Knob settings without WRITE are not stored

The [knob observation](sound-knobs-control.md) restored the verified no-lock state, then
the person selected Sound 16 and turned knob A fully counterclockwise and knob B fully
clockwise with WRITE off. The screen showed pitch and volume.

The backup equals the restored target byte for byte. Outcome: **nothing stored**.

So the sound-level setting that an unlocked step plays at is live device state, not part
of a backup. A backup holds only parameter locks: the primary bytes of pattern cells, on
steps with a note or as parameter-only cells on steps without one. After a restore, an
unlocked step plays at whatever the device holds at that moment, which the
[resonance law test](resonance-law-results.md) saw as a resonance level of 32 to 39 on
first play. An editor cannot set a sound's base knob values through a backup; it should
write locks instead.

- [Registration](../experiments/sound-knobs-registration-001.json)
- [Result](../experiments/sound-knobs-result-001.json)
- [Observation](../experiments/observe-sound-knobs-001/hardware-observation-001.json)
- Export: `experiments/exported-sound-knobs-001/project.json`

The [parameter-only lock test](param-only-control.md) asks whether a lock on an empty
step sets the held value.
