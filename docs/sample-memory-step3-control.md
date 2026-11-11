# Sample-memory step to 917504 codes

The device carries 815104 codes. This step raises the total to 917504 codes, 39.1 s of
the advertised 40 s. All empty slots are used, so the room comes from drum Sound9, whose
16 keys borrow windows of Sound1's buffer. The importer now gives such a slot its own kit:

- **Sound9** gets 16 tones of 272 ms at 450 * 2^((k-1)/12) Hz in its own 102400-code
  buffer, owned by sound id 8.
- **Sound1's buffer** and Sound10's references into it stay unchanged.

Pattern 1 plays Sound9 key k on step k. Each hit is cut by the next step.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly.
- **Pitch.** `sound9_key_k` predicts +100 (k-1) cents relative to step 1.
- **Absolute pitch.** Step 1 within 20 cents of 450 Hz.

The restore lasts about 4.1 minutes, and the backup about as long. Use fresh batteries.
If the device shows ERR or the backup differs, the limit lies between 815104 and 917504
codes, or converting a borrowed kit failed; the backup diff separates the two.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-sample-memory-003
.\.venv\Scripts\python.exe -m scripts.check_sample_memory_step3
```

- [Registration](../experiments/sample-memory-registration-003.json)
