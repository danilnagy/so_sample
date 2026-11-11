# FX 9, 10, 12 and 13 at 120 BPM: all four follow the step

The [FX onsets observation](fx-onsets-120-control.md) held FX 9, 10, 12 and 13 over steps 5
to 12 of the sixteen-key run at 120 BPM, where a step lasts 125 ms. The backup equals the
target exactly and the control run is plain in both cycles. The two cycles agree exactly.

| FX | At 120 BPM, steps 5 to 12 | Compared with 60 BPM |
| --- | --- | --- |
| 9 | every note reads -5 dB 50 ms in: cut to roughly half a step | the cut at 140 ms of a 250 ms step was also about half a step |
| 10 | of each four steps, the third has two onsets at -8 dB and the fourth is silent | the same pattern, so the gate is step-relative |
| 12 | every held step plays key 5, the first held step, once per step | the 250 ms retrigger at 60 BPM was one step too: FX 12 retriggers the first held step on every step |
| 13 | steps 7 and 11, the third of each four, play the previous step's key | at 60 BPM those steps carried a second onset of an earlier note; the effect repeats a recent note on the third of every four steps |

So these four timing effects scale with the step, like the loops of FX 1, 2 and 3. Only
FX 4 keeps a fixed time. The [FX reference](fx-reference.md) is updated.

- [Registration](../experiments/fx-onsets-120-registration-001.json)
- [Decision](../experiments/fx-onsets-120-decision-001.json)
- [Observation](../experiments/compiled-fx-onsets-120-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-fx-onsets-120-001/project.json`
