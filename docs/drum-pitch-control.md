# Drum pitch test

The pitch code is verified on melodic notes: one semitone per code around 13. Drum notes
so far always used code 13. This test plays Sound16 key 1, an 800 Hz tone, on every step
of Pattern 1, with pitch codes 13, 15, 17, 19, 21, 23, 25, 11, 9, 7, 5, 3, 1, 14, 12 and 13.
The melodic notes are cleared and the chain is reset to Pattern 1.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly.
- **semitone_per_code.** Each step sounds 100 (code - 13) cents from step 1.
- **no_transposition.** Every step sounds at the same pitch.
- **Absolute pitch.** Step 1 within 20 cents of 800 Hz.

Measurements use 20 ms windows 50 to 90 ms after each step, past the glide seen on
melodic notes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-drum-pitch-001
.\.venv\Scripts\python.exe -m scripts.check_drum_pitch_test
```

- [Registration](../experiments/drum-pitch-registration-001.json)
