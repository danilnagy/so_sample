# Effect position map: four notes, effect on steps 5 and 13

Footer byte 0 is confirmed: its high nibble holds step 1 and its low nibble step 2
([results](pattern1-FX-order-pitch-track-results.md)). This control tests whether the
other bytes follow in sequence, byte k holding steps 2k+1 and 2k+2.

Pattern 1 gets the same Sound 3 note on steps 1, 5, 9 and 13. The footer is
`FF FF 6F FF FF FF 6F FF`, placing the rising effect code 6 on byte 2's and byte 6's
high nibbles. Everything else matches the verified single-tone backup.

| Model | Step 1 | Step 5 | Step 9 | Step 13 |
| --- | --- | --- | --- | --- |
| Sequential, high nibble first | none | effect | none | effect |
| Effect on steps without notes, as in reversed orders | none | none | none | none |

Each note is classified 20 to 130 ms after its onset with the frozen thresholds: effect
at 10% or more above 1190.417 Hz, none within 1%. A model needs exactly these four
steps, each matching in its five-loop median and at least four of five loops. Anything
else is inconclusive. See the
[registration](../experiments/pattern1-FX-position-map-registration-001.json) and the
frozen [method](../scripts/pattern1_fx_multi_step_pitch_method.py).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-FX-position-map-001
.\.venv\Scripts\python.exe -m scripts.check_pattern1_fx_position_map
```
