# Observe the knobs without WRITE

An unlocked step plays at a sound-level setting. Earlier knob tests held WRITE, which
records parameter locks into the pattern. This observation turns Sound 16's knobs with
WRITE off, to find where, if anywhere, that setting is stored.

The harness first restores the verified [no-lock](no-lock-results.md) state. Then it
asks you to:

1. Keep playback stopped and WRITE off.
2. Select Sound 16: hold SOUND and press key 16.
3. Turn knob A fully counterclockwise, then knob B fully clockwise.
4. Note the parameter names the screen shows.

Don't press WRITE, play or any pattern key before the backup. There is no playback
recording this time.

The backup is classified as one of:

- nothing stored
- global records only
- Sound 16 pattern cells only
- sample or reference records only
- mixed

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/observe-sound-knobs-001
.\.venv\Scripts\python.exe -m scripts.check_knob_observation
```

- [Registration](../experiments/sound-knobs-registration-001.json)
