# FX catalogue observation

The effects footer and its code map are verified, but only FX 7's sound has been
described. A preview engine needs a description of every effect. This observation plays
Sound 8's C5 tone, 784 Hz and 200 ms at key 1, on odd steps with one effect per note:
Pattern 2 carries FX 1 to 8 and Pattern 3 FX 9 to 15, with Pattern 3's step 15 left plain
as the control. Even steps are empty so tails and repeats show. Chain 2, 3; tempo 60.

A new frozen method, `scripts/fx_descriptor_method.py`, describes each note over the step
and the step after it: onsets, and the level and dominant frequency in eleven 40 ms
windows, against the control's loudest window.

Registered before the session:

- **exact_reception.** The backup equals the target exactly.
- **control_plain.** The control has one onset, stays within 20 cents of 784 Hz, and
  leaves nothing above -30 dB in the following step.

Everything else is description, not prediction. The restore lasts about 75 seconds. Your
own notes on what each effect did are welcome at the end of the session.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-catalog-001
.\.venv\Scripts\python.exe -m scripts.check_fx_catalog_observation
```

- [Registration](../experiments/fx-catalog-registration-001.json)
