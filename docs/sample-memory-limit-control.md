# Sample-memory limit test: exactly 241 pages

When offered 249 pages, the device [kept the first 241](sample-memory-step4-results.md).
This test offers exactly 241 pages, 987136 codes, with every key reference present:

1. Sound16 gets 16 tones at 800 * 2^((k-1)/12) Hz, 181.3 ms each, in 17 pages.
2. Sound10 gets its own 102400-code kit, as in the over-limit step.

Pattern 1 plays Sound16 key k on step k. Sound16 is the last kit in the stream, so it
shows whether the end of memory holds complete data.

Registered before the session:

- **limit_is_241_pages:** the backup equals the target exactly, all 16 Sound16
  references included.
- **Pitch:** +100 (k-1) cents relative to step 1, and step 1 within 20 cents of 800 Hz.
- **Duration:** each step sounds for 181.3 ms within 5 ms.

The restore lasts about 4.4 minutes. Use fresh batteries. If the device shows ERR, finish
the session and describe it when asked.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-sample-memory-limit-001
.\.venv\Scripts\python.exe -m scripts.check_sample_memory_limit
```

- [Registration](../experiments/sample-memory-limit-registration-001.json)
