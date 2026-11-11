# Sample-memory step to 815104 codes

The device carries 675840 codes. This step raises the total to 815104 codes, 34.8 s of
the advertised 40 s, using only import kinds already verified:

1. Sound11 gets its 16 hits again in a full 102400-code buffer.
2. Sound12 gets its 16 hits again in a full 102400-code buffer.
3. Empty melodic Sound6 gets a 1.2 s, 700 Hz tone in 36864 codes.

Pattern 1 plays Sound11 key k on step k again. Its hits and windows are unchanged, so the
[drum-kit import](drum-kit-import-results.md) models apply: -100 (k-1) cents, 1500 Hz at
step 1, and each hit stopping at its window end.

The restore lasts about 3.7 minutes, and the backup about as long. If the device shows
ERR or the backup differs, the memory limit lies between 675840 and 815104 codes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-sample-memory-002
.\.venv\Scripts\python.exe -m scripts.check_sample_memory_step2
```

- [Registration](../experiments/sample-memory-registration-002.json)
