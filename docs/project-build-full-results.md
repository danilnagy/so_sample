# Full project build: exact and at tempo; two checks mis-designed

The [full project build](project-build-full-control.md) filled the device from one spec:
eight melodic imports, eight drum kits, sixteen patterns with notes, locks and effects, a
chain of eight, tempo 128 and swing 6. The backup equals the built target exactly. Total
sample memory is 196608 codes and the restore took 58 s.

| Check | Result |
| --- | --- |
| Reception | exact |
| tempo_128 | holds: Sound 13 onsets 0.4684 s apart against 0.4688 |
| chain_8 | fails by design: the snare band, 1890 to 2310 Hz, contains the kick at 1950 Hz, so the detector found kicks, not snares |
| melody_first_note | fails by design: the 200 ms melody note outlasts the 117 ms step at 128 BPM, so step 2 still carries it, 7 dB down instead of 20 |

Both failures stay on record as failures of the registered design. An exploratory reading
of the chain, from which melodic sound is loudest at the start of each pattern, confirms
what the chain check was meant to show: patterns 1 to 8 each play their own melody sound,
in order, and the sequence repeats exactly across the two recorded cycles.

So the builder handles a device-filling project: sixteen imports, all sixteen patterns,
locks, effects, chain, tempo and swing, in one restore the device accepts byte for byte and
plays at the intended tempo and order.

- [Registration](../experiments/project-build-full-registration-001.json)
- [Build report](../experiments/project-build-full-001/build-report.json)
- [Decision](../experiments/project-build-full-decision-001.json)
- [Observation](../experiments/project-build-full-001/compiled/hardware-observation-001.json)
- Current genuine export: `experiments/exported-project-build-full-001/project.json`
