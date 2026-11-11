# Independent middle-key results

The user completed the fixed-Step5 Sound3 key16-to-key7 control and supplied the capture.
All **511** native packet checksums validate with the normal0.0063 crossing profile;
measured-clock recovery was not needed for this recording. All control invariants and
both separately preregistered hypotheses pass.

Only auxiliary byte **834** changes **FF→F6**. Primary `0df883`, samples, Steps1/9/13,
other patterns and every unrelated plain packet remain unchanged. The native body hash is
`6b4f5fd40b5b7c66a754c7a6f2d870015e69e225f24a2fe9730a6f3a135705ff`.
The source WAV hash is
`19d2e80e347e229081a8363668807a5ca269f8645820d59224a3f6d974cb245c`.
See [registered results](../experiments/melodic-key7-results-001.json).

The independent middle point supports index6, alongside the previously observed0/1/15:

| Sound3 keyboard key | Auxiliary byte |
| ---: | --- |
| 1 | F0 |
| 2 | F1 |
| 7 | F6 |
| 16 | FF |

The `set-note-key` writer now accepts **only these four calibrated keys** and their
known auxiliary values. It retains the known primary0df883, one matching Sound3 cell,
unchanged upper nibble and all unrelated bytes. Unobserved keys and other sound slots
remain rejected. This is broader calibrated support, not a claim that every keyboard
value has been hardware tested.

The writer reproduces the whole physical key16 body from the prior key2 baseline,
reproduces this key7 body from the endpoint, and returns exactly to the endpoint and
alternating-key baselines with inverse edits. Those independent physical comparisons
and source preservation are covered by regression tests.

The next generated phrase keeps four evenly spaced notes at Steps1/5/9/13 and assigns
keys **1/2/7/16**. Only auxiliary834 F6→F1,898 F0→F6 and962 F1→FF change from this saved
state. Full software roundtrip passes; the generated use of keys7/16 still needs
[the four-key hardware test](native-four-keys-restore-test.md).
