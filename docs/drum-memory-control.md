# Sample-memory step to 675840 codes

The largest total of sample buffers the device has carried is 266240 codes, 11.4 s. The
device advertises 40 s of sample memory, which would be 937500 codes at 23437.5 Hz. This
test raises the total to 675840 codes, 28.8 s, by importing a full 16-hit kit into each
of empty Sound13, 14, 15 and 16, each 102400 codes.

Each hit is a 272 ms tone. Kit N uses BASE * 2^((k-1)/12) Hz, with BASE 300, 400, 600 and
800 Hz. Pattern 1 plays Sound16, the last kit written, key k on step k; each hit is cut
by the next step.

The restore lasts about three minutes, and the backup about as long.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly, all kits included.
- **Pitch.** `sound16_key_k` predicts +100 (k-1) cents relative to step 1.
- **Absolute pitch.** Step 1 within 20 cents of 800 Hz.

If the device shows ERR or the backup differs, the failure is the result: it bounds
the memory limit between 266240 and 675840 codes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-drum-memory-001
.\.venv\Scripts\python.exe -m scripts.check_drum_memory_test
```

- [Registration](../experiments/drum-memory-registration-001.json)
