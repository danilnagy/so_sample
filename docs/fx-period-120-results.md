# Tempo sync: FX 1, 2 and 3 follow the tempo, FX 4 does not

The [tempo-sync test](fx-period-120-control.md) repeated the loop-period measurement at
120 BPM. The backup equals the target exactly and the control note has no period.

## Registered result

Neither registered model holds. `tempo_synced` fails because FX 4 kept its period;
`fixed_ms` fails because FX 1 halved. The method resolved FX 1 (120 ms) and FX 4 (80 ms)
and left FX 2, 3 and 12 unresolved, their tracks being mostly flat with periodic glitches.

## Exploratory reading of the tracks

| FX | 60 BPM | 120 BPM | Reading |
| --- | --- | --- | --- |
| 1 | 250 ms | 120 ms | follows the tempo: 1/16 of a bar |
| 2 | 333 ms | glitches every 160 ms | follows the tempo: 1/12 of a bar |
| 3 | 125 ms | glitches every 60 ms | follows the tempo: 1/32 of a bar |
| 4 | 80 ms | 80 ms | fixed time, about 80 ms |
| 12 | 250 ms | glitches every 60 ms within a 250 ms cycle | retrigger; its relation to tempo is unresolved |

So three of the four loop effects are musical divisions of the bar and one is a fixed
80 ms stutter. For a preview engine: FX 1, 2 and 3 loop 1/16, 1/12 and 1/32 of the bar at
the current tempo from the point where the effect starts; FX 4 loops 80 ms regardless.

- [Registration](../experiments/fx-period-120-registration-001.json)
- [Decision](../experiments/fx-period-120-decision-001.json)
- [Measurements](../experiments/compiled-fx-period-120-001/fx-period-120-measurements-001.json)
- [Observation](../experiments/compiled-fx-period-120-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-period-120-001/project.json`
