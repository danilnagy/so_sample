# FX rules test: FX 14's restart and FX 13's source note

Two effects still lack a rule. FX 14 held from step 5 replayed keys 1 to 4 over and over,
and held from step 2 replayed key 1. FX 13 replaced the third of every four steps with a
recent note, the previous step's at 120 BPM and two steps earlier in one case at 60 BPM.

Patterns 1 to 5 play Sound 8's tone with keys 1 to 16 in order at tempo 60:

| Pattern | Effect | Held on steps |
| --- | --- | --- |
| 1 | 14 | 3 to 16 |
| 2 | 14 | 7 to 16 |
| 3 | 14 | 9 to 16 |
| 4 | 14 | 5 to 12 |
| 5 | 13 | 2 to 16 |
| 6 | none | control |

Registered before the session, as the key heard 100 ms into each held step:

- **FX 14.** `loop_steps_before_hold`: the steps before the hold repeat, so a hold from
  step 7 cycles keys 1 to 6. `loop_power_of_two`: the same but rounded down to a power of
  two, so a hold from step 7 cycles keys 1 to 4. `restart_every_four`: always four.
- **FX 13.** `previous_on_third`: the third step of every four plays the previous step's
  key. `two_earlier_on_third`: it plays the key from two steps earlier. `unchanged`.

A rule holds when it matches every held step of every pattern using that effect. Keys at
30 ms and onset counts are reported as well. The restore lasts about a minute.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-fx-rules-001
.\.venv\Scripts\python.exe -m scripts.check_fx_rules_test
```

- [Registration](../experiments/fx-rules-registration-001.json)
