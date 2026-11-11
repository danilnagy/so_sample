# Fixed-step key2 control results

The user completed the requested Sound3 key1-to-key2 replacement at Pattern1 Step5 and
supplied the capture. All **511** native packet checksums validate. Every preservation
and locality check passes, and **both separately preregistered hypotheses fit**.

Only Pattern1 auxiliary byte **834** changes, **F0→F1**, in plain packet index7.
Primary bytes[198,201) remain `0df883`. Steps1/9/13, sample packets, other patterns and
every unrelated packet remain unchanged. Native body SHA-256 is
`82d11b01d01f04708b099c3e36f50f2474c09a2aaa85fa68f2511286a0159307`.
Source WAV SHA-256 is
`ff78fa4c5b29b4b1ec4df8fdfa89cec54020da7e9059b3b342c78672edd9d90d`.
See [registered results](../experiments/melodic-key2-results-001.json).

This locally supports keyboard index0/1 in the auxiliary low nibble for **Sound3 keys1/2**.
The upper nibble remains opaque and unchanged. It does not establish other keys, other
sounds, gate semantics or the primary parameter bitfields. The older drum auxiliary10/11
values are consistent with a related index distinction, but no actual historical slice
selection is inferred from this melodic experiment.

The narrow experimental `set-note-key` writer accepts only Sound3 keys1/2, exactly one
matching primary/auxiliary cell at the source step, primary `0df883` and auxiliaryF0/F1.
It changes the low nibble while preserving all other pattern and packet bytes. Unknown
keys, sounds, primary parameters, upper-nibble values and unsupported source layouts are
rejected. Source captures and artifacts are preserved.

Applying the writer to the genuine key1 baseline reproduces this recorded key2 body's
entire encoded packet stream exactly. Its inverse reproduces the genuine key1 baseline.
These are software comparisons against separate physical captures, not a generated
key-edit hardware restore result.

The first generated key edit starts from this physical key2 capture and changes Step13
to key2. Pattern1 then has keys **1,2,1,2** at Steps **1,5,9,13**. Only byte962 changes
F0→F1. Full software waveform/count roundtrip and all packet checks pass; its own
hardware test is [the alternating-key restore](native-note-key-restore-test.md), now
completed with explicit user confirmation and an exact measured-clock recapture match.
