# Drum pitch codes: one semitone per code

The [drum pitch test](drum-pitch-control.md) played Sound16 key 1, an 800 Hz tone, on
every step with pitch codes from 1 to 25. The backup equals the compiled target exactly.
The person heard one drum sound at changing pitches.

`semitone_per_code` holds on all 16 steps in at least 4 of 5 loops; `no_transposition`
fails. Step 1, code 13, sounds at 799.9 Hz, the stored rate. Code 25 sounds +1198 cents
and code 1 -1200 cents.

Steps that follow a lower note read 2 to 3 cents flat 50 to 90 ms after the step, and
step 16 reads -3.4 cents after code 12. Drum notes appear to glide like melodic notes,
with a slightly longer tail than the window allows for. This is an exploratory reading,
within the 20-cent tolerance.

So a drum note's pitch code transposes its slice by code - 13 semitones from the stored
rate, the same law as melodic notes without their fixed +7 semitone offset.

- [Registration](../experiments/drum-pitch-registration-001.json)
- [Decision](../experiments/drum-pitch-decision-001.json)
- [Observation](../experiments/compiled-drum-pitch-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-drum-pitch-001/project.json`

The next [filter law test](filter-law-control.md) measures every filter code.
