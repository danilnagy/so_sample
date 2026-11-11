# Per-step volume law

Volume is bits 6 to 11 of a note's primary bytes, codes 0 to 63. Earlier generated
restores measured volume 18 at 0.8189 and volume 36 at 2.2036 times volume 21, which no
single simple law fits exactly. This test maps the gain across the range.

Through the public plan path, all 16 Sound 3 notes are set to pitch 13 and key 1, and
each step gets its own volume code: 36, 0, 63, 9, 54, 18, 45, 27, 3, 60, 12, 48, 21, 39, 6,
30. Each note's level is the RMS 50 to 90 ms after its grid onset, median over five loops,
in dB relative to step 1 (volume 36). Two laws fitted to the earlier points are
registered: amplitude proportional to code^1.38, and 0.5 dB per code. A law needs every
nonzero code within 1.5 dB; code 0 is reported only. The measured gain table is the main
result either way. Level also depends on pitch, because higher pitches play the sample
faster, so all notes here share one pitch. See the
[registration](../experiments/volume-law-registration-001.json) and
[method](../scripts/pattern1_volume_gain_method.py).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-volume-law-001
.\.venv\Scripts\python.exe -m scripts.check_volume_law_test
```

If the playback check reports a peak near full scale, lower the PO-33 volume and record
the playback again; the harness offers the retry. Only level ratios within one recording
matter.
