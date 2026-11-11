# Sample-memory step past the advertised 40 s

The device carries 917504 codes, 39.1 s. This step gives drum Sound10 its own 102400-code
kit the same way Sound9 got one, raising the total to 1019904 codes, 43.5 s. The
advertised limit is 40 s, 937500 codes.

Registered before the session:

- **advertised_limit_rejects** predicts the backup differs from the target.
- **accepted** predicts the backup equals the target exactly.

The backup is classified as accepted exactly, kept the previous contents, empty, other
content, or not decoded. Only if it is accepted exactly is Pattern 1's playback of Sound10
measured: +100 (k-1) cents, and step 1 within 20 cents of 350 Hz.

The restore lasts about 4.5 minutes. Use fresh batteries. Run the whole session even if
the PO-33 shows ERR: the backup records what the device kept. If the harness reports a
mismatch and asks to record another backup, answer no. Describe anything unusual when it
asks.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-sample-memory-004
.\.venv\Scripts\python.exe -m scripts.check_sample_memory_step4
```

- [Registration](../experiments/sample-memory-registration-004.json)
