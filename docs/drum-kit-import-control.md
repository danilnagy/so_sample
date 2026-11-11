# First software drum-kit import

Sixteen generated WAV hits replace the device-recorded kit in drum Sound11, using the new
importer in `src/po33_re/drum_import.py`. It writes the layout the device writes when it
records: one buffer owned by the slot's first sound id, whose header is key 1's window,
and 15 references with contiguous windows in key order. The capacity stays at the
observed 102400 codes, so total sample memory is unchanged.

Hit k is a tone at 1500 * 2^(-(k-1)/12) Hz, 100 cents below the hit before. It lasts
1750 + 250 (k-1) native codes, from 74.7 to 234.7 ms. Pattern 1 already plays Sound11
key k on step k.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly.
- **Slice per key.** `new_kit_key_k` predicts -100 (k-1) cents relative to step 1;
  `old_kit_still_playing` predicts +150 (k-1). Same frozen grid method and tolerances as
  the [drum-notes test](drum-notes-writer-results.md).
- **Absolute pitch.** Step 1 within 20 cents of 1500 Hz.
- **Duration.** `stops_at_window_end` predicts each step sounds for its window length,
  within 5 ms, using the frozen method in `scripts/drum_slice_duration_method.py`.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-drum-kit-import-001
.\.venv\Scripts\python.exe -m scripts.check_drum_kit_import_test
```

- [Registration](../experiments/drum-kit-import-registration-001.json)
- Hits (`experiments/drum-kit-hits-001`, a local research artifact, not in the repository)
