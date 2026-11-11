# Melodic notes writer: hardware verified

The [registered writer test](melodic-notes-writer-control.md) passed. A plan compiled
through `apply-edits` with `set_melodic_notes` wrote the melody 16, 1, 15, 2, 14, 3, 13,
4, 12, 5, 11, 6, 10, 7, 9, 8 on Sound 3. The backup matched the compiled target
exactly, and every step's pitch matched the interval predicted by the confirmed key
layout within one cent:

| Step | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Predicted cents | 0 | 1400 | -200 | 1500 | -300 | 1700 | -500 | 1800 | 600 | 700 | 500 | 900 | 300 | 1000 | 200 | 1200 |
| Measured cents | 0 | 1400.2 | -200.0 | 1500.1 | -299.4 | 1700.2 | -499.6 | 1800.2 | 600.2 | 700.4 | 500.3 | 899.9 | 300.0 | 1000.0 | 199.7 | 1200.1 |

The person confirmed that the melody jumped between low and high notes. See the
[decision](../experiments/melodic-notes-writer-decision-001.json) and
[observation](../experiments/compiled-melodic-notes-writer-001/hardware-observation-001.json).
Current genuine export: `experiments/exported-melodic-notes-writer-001/project.json`.

Scope: Sound 3 notes sharing one set of parameters. Other melodic sounds use the same
cell layout and are expected to share the key layout; that was not measured.
