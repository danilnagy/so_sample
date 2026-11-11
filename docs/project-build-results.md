# A project built from a spec plays as built

The [project build test](project-build-control.md) assembled a small song with
`po33_re.project_build`: two sample imports, two patterns with notes, parameters, a lock
on an empty step and an effect, a four-pattern chain, tempo 100 and swing 4. The backup
equals the built target exactly. The person heard a small beat with a melody and a
filtered second half.

| Check | Expected | Measured |
| --- | --- | --- |
| Sound 13 onset spacing | 0.600 s | 0.5997 s |
| Sound 9 offset after the preceding Sound 13 | 0.175 s | 0.1765 s |
| Melody first note, 784 Hz, step 1 over step 2 | at least 20 dB | 32.8 dB |

`project_plays_as_built` holds. Tempo, swing, chain, imports, explicit-parameter notes,
parameter-only locks and the effects footer all came through one build. The new
`set_notes` writer needs no template note, and `set_tempo_byte` writes tempo in any global
layout.

For an editor this is the whole path: a description of samples and patterns becomes a
restore file that the device accepts byte for byte and plays at the intended tempo and
feel.

- [Registration](../experiments/project-build-registration-001.json)
- [Build report](../experiments/project-build-001/build-report.json)
- [Decision](../experiments/project-build-decision-001.json)
- [Observation](../experiments/project-build-001/compiled/hardware-observation-001.json)
- Current genuine export: `experiments/exported-project-build-001/project.json`
