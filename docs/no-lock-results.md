# Code 0 means no parameter lock

The [no-lock test](no-lock-control.md) placed code-0 steps between locked filter and
resonance values in two chained patterns. The backup equals the compiled target exactly.

## Registered hypotheses

- **zero_holds_last_lock** fails on 2 of 18 steps. 16 code-0 steps match the last locked
  step of their pattern within 0.82 dB. The two exceptions follow filter code 10: 1.74 and
  2.06 dB.
- **zero_filter_is_off** fails clearly. Filter code-0 steps differ from the bypass by up
  to 41 dB, unless the held value is itself 63.

## Exploratory reading

Filter code 10 attenuates the sawtooth by about 42 dB, close to the noise floor. Each
filter-10 step differs from itself by 1.4 to 1.9 dB from one cycle to the next. Their
median responses match the held step within 0.1 dB on the first ten harmonics. The two
failures are noise at that level, not a different sound.

So, for filter and resonance, code 0 means no parameter lock: the step keeps the last
locked value. Volume code 0 behaves the same way
([volume law results](volume-law-results.md)). An editor should treat 0 as "unlocked",
not as a value.

- [Registration](../experiments/no-lock-registration-001.json)
- [Decision](../experiments/no-lock-decision-001.json)
- [Observation](../experiments/compiled-no-lock-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-no-lock-001/project.json`

The [knob observation](sound-knobs-control.md) looks for where the unlocked sound-level
setting is stored.
