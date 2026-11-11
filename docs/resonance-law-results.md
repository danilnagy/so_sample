# Resonance law: eight levels, and code 0 is no lock

The [resonance law test](resonance-law-control.md) played the sawtooth through low-pass
filter 16 with every resonance code. The backup equals the compiled target exactly. The
person heard the tone ring more across the five patterns.

## Registered hypotheses

| Hypothesis | Result |
| --- | --- |
| reference_consistent | Holds: references agree within 0.02 dB |
| peak_rises | Fails: code 0 peaks at +9.4 dB, above codes 1 to 47 |
| strong_at_63 | Fails: code 63 is only 3.7 dB above code 0 |
| peak_near_edge | Holds: every peak of +3 dB or more is at 800 or 1000 Hz |

Both failures come from code 0, which turns out not to be the lowest resonance.

## Exploratory reading

Resonance has **eight levels**, one per block of eight codes. Each code within a block
gives an identical response:

| Codes | Peak response | Peak frequency |
| --- | --- | --- |
| 1-7 | -6.8 dB | 200 Hz |
| 8-15 | -2.8 dB | 200 Hz |
| 16-23 | -0.3 dB | 200 Hz |
| 24-31 | +1.2 dB | 800 Hz |
| 32-39 | +3.8 dB | 800 Hz |
| 40-47 | +5.8 dB | 1000 Hz |
| 48-55 | +8.9 dB | 1000 Hz |
| 56-63 | +13.1 dB | 1000 Hz |

The peak rises by about 20 dB from the lowest level to the highest, close to the filter
edge. Low levels also lower the whole passband.

**Code 0 behaves as no parameter lock.** Each code-0 step sounded like the last step
with a nonzero resonance:

| Occurrence | Previous locked code | Peak |
| --- | --- | --- |
| first in the recording | none | +3.8 dB, the 32-39 level |
| after 63 | 63 | +13.0 dB |
| after 47 | 47 | +5.8 dB |
| after 63 | 63 | +13.1 dB |

This also explains the earlier findings. Volume code 0 played at the previous step's
level. Filter code 0 measured flat right after a bypass step. The filter law test ran with
resonance 0 on every step, so it measured at the held 32-39 level. The
[no-lock test](no-lock-control.md) checks the rule directly.

- [Registration](../experiments/resonance-law-registration-001.json)
- [Decision](../experiments/resonance-law-decision-001.json)
- [Observation](../experiments/compiled-resonance-law-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-resonance-law-001/project.json`
