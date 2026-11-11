# Effect order confirmation with a frozen pitch track

The [single-tone F6/6F pair](pattern1-single-tone-FX-order-results.md) was received
exactly, but its steady-tone comparison was inconclusive because the effect fades in
over its step. An exploratory pitch track pointed to step 1 being the footer's high
nibble. This control freezes that pitch track as a method and tests it on fresh
recordings of the same two restores.

| Leg | Folder | Footer byte 0 | High nibble first predicts | Low nibble first predicts |
| --- | --- | --- | --- | --- |
| A | `experiments/edited-pattern1-single-tone-FX-F6-002` | F6 | step 1 none | step 1 effect |
| B | `experiments/edited-pattern1-single-tone-FX-6F-002` | 6F | step 1 effect | step 1 none |

## Decision, registered before the fresh recordings

- Both legs must be received exactly, with only footer byte 0 changed.
- Step 1 is examined 20 to 130 ms after each loop's onset, in audible windows only. It is
  "effect" if the pitch reaches 10% above the 1190.417 Hz reference, and "none" if it
  stays within 1%. Anything between is indeterminate.
- A model is supported only if both legs' five-loop medians and at least four of the
  five individual loops match its prediction. Otherwise the result is inconclusive.

The method was developed on the -001 recordings, where it gives A none at 1.000 and
B effect at 1.44. Those recordings are not evidence for this test. See the
[registration](../experiments/pattern1-single-tone-FX-order-pitch-track-registration-001.json)
and the frozen [method](../scripts/pattern1_fx_step_pitch_method.py).

## Steps

Run A, then B, then the check:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-single-tone-FX-F6-002
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-single-tone-FX-6F-002
.\.venv\Scripts\python.exe -m scripts.check_pattern1_fx_order_pitch_track
```
