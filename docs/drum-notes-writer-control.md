# Drum-notes writer test

Pattern 1 gets drum Sound11 key k on step k, for keys 1 to 16, through the public
`set_drum_notes` plan operation. Key k is written as auxiliary byte 0x10 + k - 1. The
device has recorded keys 1 and 2 this way; keys 3 to 16 are new values. The Sound3 and
Sound7 notes in Pattern 1 are cleared so Sound11 plays alone.

The source is the device's own backup after the [drum recording](drum11-record-observation-results.md),
so slice k holds a tone burst at 400 * 2^((k-1)/8) Hz, 150 cents above the slice before.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly.
- **Slice per key.** Model `key_k_plays_slice_k` predicts 150 * (k - 1) cents relative to
  step 1; `every_key_plays_slice_1` predicts 0 on every step. Frozen grid method,
  20 ms windows 15 to 55 ms after each grid onset, 20-cent tolerance, at least 4 of 5 loops.
- **Absolute pitch, secondary.** Step 1 against the 400 Hz burst: `stored_rate` predicts
  0 cents and `plus_7_semitones` predicts +700 cents, the offset melodic sounds show at key 1.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-drum-notes-001
.\.venv\Scripts\python.exe -m scripts.check_drum_notes_writer_test
```

- [Registration](../experiments/drum-notes-registration-001.json)
- [Plan](../experiments/drum-notes-plan-001/plan.json)
