# Filter law test: every filter code

Earlier tests found that filter code 63 is the audible bypass. Code 1 is a full low-pass,
62 a full high-pass, 16 a partial low-pass and 52 a partial high-pass. The cutoff for
every other code is unknown.

This test measures all codes in one session:

- **Sample.** Sound16 gets a kit of 200 Hz sawtooth hits with 55 harmonics. Drums play
  at the stored rate, so the harmonics stay at multiples of 200 Hz.
- **Patterns.** Patterns 1 to 5 each play Sound16 on all 16 steps, with resonance 0.
  Step 1 of each pattern is the bypass, code 63. The other 75 steps cover codes 0 to 62,
  with some repeated.
- **Chain.** The chain 1, 2, 3, 4, 5 plays them in turn. Playback records two cycles,
  44 seconds.

A new frozen method, `scripts/filter_response_method.py`, measures each harmonic against
the bypass steps. It classifies each code as low-pass, high-pass, flat or silent, and
finds its -3 dB edge.

Registered before the session:

- **reference_consistent.** Every bypass step agrees with its cycle reference within 0.5 dB.
- **low_codes_low_pass.** Codes 1 to 31 are low-pass, flat or silent. Codes 1 to 16 are
  low-pass or silent.
- **high_codes_high_pass.** Codes 32 to 62 are high-pass, flat or silent. Codes 47 to 62
  are high-pass or silent.
- **edges_monotonic.** Within each type the edge rises with the code.

You should hear one buzzy tone that gets darker, then thinner, across the five patterns.
The restore lasts about 3.4 minutes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-filter-law-001
.\.venv\Scripts\python.exe -m scripts.check_filter_law_test
```

- [Registration](../experiments/filter-law-registration-001.json)
