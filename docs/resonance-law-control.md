# Resonance law test

Filter code 16 is a low-pass with its -3 dB edge near 1400 Hz at resonance 0. This test
keeps the sawtooth kit and five-pattern chain from the [filter law test](filter-law-results.md).
Every step except the first in each pattern gets filter 16, with resonance codes 0 to 63
spread over the five patterns and some repeated. Step 1 of each pattern is the bypass
reference, filter 63 with resonance 0.

Registered before the session, using the same frozen method:

- **reference_consistent.** Every reference step agrees within 0.5 dB.
- **peak_rises.** The peak response never falls by more than 0.5 dB from one resonance
  code to the next.
- **strong_at_63.** Resonance 63 peaks at least 10 dB above resonance 0.
- **peak_near_edge.** Any peak of +3 dB or more lies between 700 and 2800 Hz.

You should hear the tone ring or whistle more across the five patterns. The restore
lasts about 3.4 minutes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-resonance-law-001
.\.venv\Scripts\python.exe -m scripts.check_resonance_law_test
```

- [Registration](../experiments/resonance-law-registration-001.json)
