# Bit-5 glide test

In the [note bits test](note-bits-results.md), notes with bit 5 set were shorter than
their partners, but only the partners followed a pitch change. This test puts a pitch
change before every note. Pattern 2 plays Sound 1 on every step, pitch codes alternating
7 and 25. Bit 5 is clear on steps 1 to 8 and set on steps 9 to 16.

Each step is read twice with the frozen grid method: early, 5 to 35 ms after the onset,
where a glide from the previous pitch still shows; late, 100 to 140 ms. Levels and the
pitch-25 durations are read as before.

Registered before the session:

- **bit5_inert.** Flagged steps match plain steps of the same pitch early and late within
  20 cents, in level within 1.5 dB, and in pitch-25 duration within 5 ms.
- **bit5_no_glide.** Flagged steps start within 20 cents of their target while plain steps
  start at least 100 cents toward the previous pitch, and flagged pitch-25 notes are more
  than 5 ms shorter.

The restore lasts about a minute.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-bit5-glide-001
.\.venv\Scripts\python.exe -m scripts.check_bit5_glide_test
```

- [Registration](../experiments/bit5-glide-registration-001.json)
