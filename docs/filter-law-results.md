# Filter law: every code measured

The [filter law test](filter-law-control.md) played a 200 Hz sawtooth on drum Sound16
through every filter code, with a bypass reference at the start of each chained pattern.
The backup equals the compiled target exactly. The person heard the tone get darker,
then thinner.

## Registered hypotheses

| Hypothesis | Result |
| --- | --- |
| reference_consistent | Holds: bypass steps agree within 0.12 dB |
| low_codes_low_pass | Fails, on code 29 only |
| high_codes_high_pass | Holds |
| edges_monotonic | Fails, on code 29 only |

Code 29 is a low-pass whose edge lies above the measured band. Its small resonance bump,
+3.9 dB at 8 to 10 kHz, sits in the method's top band, so the frozen slope rule called it
high-pass. Both failures are that one misclassification; they stay recorded as failures.

## Exploratory reading

- **Code 0** is flat, like the bypass 63.
- **Codes 1 to 26** are low-pass. The -3 dB edge rises from 400 Hz at codes 1 to 9 to
  7 kHz at code 26. From code 10 up it follows about 2^(0.234 code + 6.66) Hz, 4.3 codes
  per octave. Codes 1 to 8 also attenuate the fundamental.
- **Codes 27 to 31** are low-pass with the edge above 10 kHz, showing only a rising
  resonance bump near the top.
- **Codes 32 to 43** are flat within 3 dB from 200 Hz to 10 kHz, so any high-pass edge
  is below 200 Hz.
- **Codes 44 to 62** are high-pass. The edge rises from 400 Hz at code 44 to 9 kHz at
  code 62, about 2^(0.262 code - 2.94) Hz, 3.8 codes per octave.

Even at resonance 0 the low-pass shows a small peak, about +3.6 dB, just below its edge.
For an editor this gives a usable map from code to cutoff. Code 63, or 0, means off.

- [Registration](../experiments/filter-law-registration-001.json)
- [Decision](../experiments/filter-law-decision-001.json)
- [Measurements](../experiments/compiled-filter-law-001/filter-measurements-001.json)
- [Observation](../experiments/compiled-filter-law-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-filter-law-001/project.json`

The next [resonance law test](resonance-law-control.md) measures resonance at filter 16.
