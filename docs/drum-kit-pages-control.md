# Drum import into an empty slot with page-rounded capacity

The importer's default capacity is now the kit length rounded up to whole 4096-code
pages, instead of the device's fixed 102400 codes. This test checks that default and an
import into an empty drum slot:

1. Sound11 gets the same 16 hits again, in 61440 codes instead of 102400.
2. Empty Sound12 gets 16 new tones, 500 * 2^((k-1)/12) Hz, each 101.3 ms, in 40960 codes.
3. Pattern 1 plays Sound12 key k on step k; Sound11's notes are cleared.

Total sample memory stays at 266240 codes, the largest the device has already carried.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly, both kits and both
  capacities included.
- **Pitch.** `sound12_key_k` predicts +100 (k-1) cents relative to step 1.
- **Absolute pitch.** Step 1 within 20 cents of 500 Hz.
- **Duration.** Every step sounds for 101.3 ms within 5 ms.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-drum-kit-pages-001
.\.venv\Scripts\python.exe -m scripts.check_drum_kit_pages_test
```

- [Registration](../experiments/drum-kit-pages-registration-001.json)
- [Plan](../experiments/drum-kit-pages-plan-001/plan.json)
