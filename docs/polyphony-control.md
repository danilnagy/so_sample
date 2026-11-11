# Polyphony test

How many sounds can play on one step? Fourteen sounds get distinct tones: the eight
melodic slots keep their 0.5 s tones, drum Sound 13 and 14 keep 300 and 400 Hz hits, and
Sound 11, 12, 15 and 16 are re-imported as kits of identical 272 ms tones at 1500, 500,
1200 and 1350 Hz. Sound 9 and 10 are left out because their hits last only 43 ms.

- **Pattern 2** plays each sound alone, one per step.
- **Pattern 3** stacks them on odd steps: 2, 4, 6, 8, 10 and 14 sounds, all 14 again,
  then the 6 drums alone.
- The chain is 2, 3. Playback records three cycles.

A new frozen method, `scripts/polyphony_method.py`, measures each voice 100 to 240 ms
into the step and calls it present when it is within 10 dB of its solo level.

Registered before the session: `voice_limit_L` for L in 2, 4, 6, 8, 10, 12 and 14
predicts that each stack sounds min(requested, L) voices. The backup must equal the
compiled target exactly. The levels of stacked voices against their solos are reported
as an exploratory reading.

You should hear single notes, then chords that get thicker. The restore lasts about
3.4 minutes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-polyphony-001
.\.venv\Scripts\python.exe -m scripts.check_polyphony_test
```

- [Registration](../experiments/polyphony-registration-001.json)
