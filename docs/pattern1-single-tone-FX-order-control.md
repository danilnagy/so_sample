# Single-tone effect order: F6 and 6F

This pair tests which nibble of Pattern 1's first footer byte controls step 1. It
builds on the verified [single-tone baseline](pattern1-single-tone-baseline-results.md):
one Sound 3 note on step 1, nothing else, all effects clear, global byte 131 = 7.

| Leg | Folder | Footer byte 0 | Low nibble first predicts | High nibble first predicts |
| --- | --- | --- | --- | --- |
| A | `experiments/edited-pattern1-single-tone-FX-F6-001` | F6 | step 1 an octave up, about 2380.8 Hz | step 1 unshifted, about 1190.4 Hz |
| B | `experiments/edited-pattern1-single-tone-FX-6F-001` | 6F | step 1 unshifted | step 1 an octave up |

Only footer byte 0 differs from the verified single-tone backup. Step 2 has no note, so
only step 1's effect is audible. The frozen first-tone window, 80 to 140 ms after the
onset, lies inside step 1, which lasts 150 ms at 100 BPM.

## Decision, registered before any capture

1. Both legs must be received exactly, with only footer byte 0 changed.
2. **Primary:** the unchanged frozen comparison of all six A/B first-tone ratios. Near 2
   within 1% supports low nibble first; near 0.5 supports high nibble first.
3. **Cross-check:** each leg's six first tones must match its model's predicted frequency
   within 1%, using the measured single-tone reference of 1190.417 Hz.
4. A model is supported only when both agree. Anything else stays inconclusive.

The earlier F6 restore's unshifted first tone suggested high nibble first. That lead was
not registered and does not count here. See the
[registration](../experiments/pattern1-single-tone-FX-order-registration-001.json).

## Steps

Run leg A, then leg B, each as one guided session. Keep the PO-33 volume, computer
volume and MIX setting unchanged across both legs, and do not press FX, enable write
or move knobs.

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-single-tone-FX-F6-001
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-single-tone-FX-6F-001
```

Each session prompts for the cable swaps, checks the backup against its target, and
records 14 s of playback after the first sound. Then run the checks:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_pattern1_fx_order_single_tone --leg a
.\.venv\Scripts\python.exe -m scripts.check_pattern1_fx_order_single_tone --leg b
.\.venv\Scripts\python.exe -m scripts.check_pattern1_fx_order_single_tone --audio
```

This is local to footer byte 0 of Pattern 1 with one note. It does not establish an
all-step or all-pattern order, and no per-step effect writer is enabled.
