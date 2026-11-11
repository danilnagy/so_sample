# Sample windows are honoured: trim by header

The [sample window test](sample-window-control.md) imported a 1.0 s four-segment sample
into Sound 6 and Sound 7 and set their header windows to segments 3 and 2. The backup
equals the compiled target exactly, nonzero starts included. The person heard two
alternating short tones.

`window_honoured` holds on every note; `start_ignored` fails.

| Sound | Window, codes | Expected | Measured pitch | Measured length |
| --- | --- | --- | --- | --- |
| 6 | 11719 to 17578 | 899.0 Hz, 166.8 ms | +0.3 cents | 168.2 ms |
| 7 | 5859 to 11719 | 749.2 Hz, 166.8 ms | +0.3 cents | 168.3 ms |

So a self-owned melodic sample plays from its header's start code to its end code. An
editor can trim a sample, or pick a region of a longer one, by rewriting those two fields
with `set_sample_window`, without re-importing audio. The same two fields are what the
device's own drum slicing and factory references use.

- [Registration](../experiments/sample-window-registration-001.json)
- [Decision](../experiments/sample-window-decision-001.json)
- [Observation](../experiments/compiled-sample-window-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-sample-window-001/project.json`
