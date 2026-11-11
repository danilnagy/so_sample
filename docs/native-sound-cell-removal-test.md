# Test removing only one sound from a step

Completed: the user confirms the lights and playback. The genuine recapture matches
the entire target with all 511 checksums valid and every unrelated note/sample intact.
See [removal results](native-sound-cell-removal-results.md). Original instructions below
are retained for provenance.

Restore **experiments/generated-sound2-remove-001/restore-remove-sound2-step1.wav**
with the previously successful stereo playback settings. Enter receive with
**write + sound + record** and play the entire 44.1 kHz stereo PCM16 transfer,
approximately 23.1 seconds.

1. Report whether restore succeeds.
2. **Before playback or step inspection**, select **Sound 8 / TONE**, with write
   off and playback stopped. Save a full stereo backup with the existing settings
   as **experiments/edited-sound2-remove-001/capture.wav**.
3. After saving, select **Sound 2** and enter write. Confirm **only Step 9 is lit**
   and **Step 1 is unlit**. Inspect **without tapping step buttons**, then exit write.
4. Select **Sound 3** and enter write. Confirm **Steps 1, 5, 9, 13 remain lit**.
   Inspect without tapping steps, then exit write.
5. Play Pattern 1 briefly and report whether it plays normally. Stop, leave write
   off and return to **Sound 8 / TONE** afterward.

Only Sound 2 primary bytes 3/4/5 and auxiliary byte 769 are cleared. Sound 3 remains
on Step 1, Sound 2 remains on Step 9, and all samples and unrelated state are preserved.
The remover accepts only occupied Sound 2 **0d2831/F0** cells with the observed optional
Sound 3 neighbour. Empty, malformed and unknown cells are rejected.

- [Software validation](../experiments/generated-sound2-remove-001/software-validation.json)
- WAV SHA-256: `c72e4567bb387eeb845aac5f56d38da9d2200b94fe1e5dda0506cdd2a876593b`
- Expected native body SHA-256: `1e493f1495ecf2dc68077a35ae97b8883acbe96b94d0798427a9f3f990a1761a`
- Exactly 511 packets, frame end 89396; only plain packet indices 4 and 7 change.

Full waveform phase/count and exact native target roundtrips pass. The inverse
remover reproduces two genuine baseline bodies exactly, and the remaining note can
be copied back to recreate the entire source body. This particular generated deletion
now has its separate hardware restore, light/playback and recapture evidence in the
completed result linked above.

The current verified source remains preserved in **experiments/edited-sound2-cell-001/capture.wav**.
Controls follow the [official PO-33 guide](https://teenage.engineering/guides/po-33/en).

Reproduce in a fresh directory:

```powershell
.\.venv\Scripts\python.exe scripts/make_sound_cell_removal_candidate.py experiments/edited-sound2-cell-001/derived/analysis-001/capture.symbols.npz --out-dir experiments/generated-sound2-remove-002
```
