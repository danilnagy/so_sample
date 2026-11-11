# Generated interior pitch and frequency interval control

Two fixed research WAVs use the verified complete minimum-return body. They replace
only first-primary low-five bits in all 16 Sound 3 / Pattern 1 cells with 13 or 14,
preserving bit 5, volume 36 and every other bit. The constructor requires that exact
genuine raw-1 body and permits only these two values. Both WAVs pass strict phase and
complete native-body/packet recovery. No public pitch operation is enabled.

| Leg | Folder | Target body SHA-256 |
| --- | --- | --- |
| First, generated 13 reference | `experiments/edited-sound3-pitch13-reference-001` | `7f09d45808d5a9064139b43f717bbc8bd8e99a9248411bc534641ff343783fdd` |
| Later, generated 14 candidate | `experiments/edited-sound3-pitch14-001` | `05e1d379603f4457fd1496e516460e0a8de50cadf0fc810e9c2f3ca1da1b4637` |

Value 13 recreates the earlier note-cell parameters associated with the measured
tone near 500.65 Hz. Parameter-only cells now also contain 13, so this is a generated
reference rather than a complete replay of that older genuine body. Value 14 probes
the next raw code. The frequency increase and ratio `2^(1/12)` are new hypotheses
selected after endpoint data, registered before either pair backup or playback audio.
One successful interval would not prove the law for all other codes.

## First physical action: reference

1. Restore `experiments/edited-sound3-pitch13-reference-001/restore.wav` through the
   established stereo path and playback level. Keep both knobs and all audio settings
   unchanged; A remains at its physical minimum.
2. Select Pattern 1 / Sound 3 / TONE, stopped with write off. Do not move a knob to
   inspect a pitch display.
3. Before playback, save a complete backup as
   `experiments/edited-sound3-pitch13-reference-001/capture.wav`, using the established
   reduced recording level and one second trailing silence.
4. Separately record 12–15 seconds of ordinary Pattern 1 playback as
   `experiments/edited-sound3-pitch13-reference-001/playback.wav`, then stop/write off.
5. Confirm restore success and recognizable pattern playback. No numeric display or
   remembered pitch comparison is required. Leave both knobs untouched.

Candidate 14 waits until the reference native capture is exact and its audio is
usable. Its WAV is already prepared; do not restore it during this reference stage.

## Frozen frequency method

Both recordings use the same third-order zero-phase 450..600 Hz band, 5 ms RMS
envelope, 0.15/0.25/0.35 peak-relative thresholds, and fits 80–180 ms after onset.
A Hann-window FFT with grid spacing at most 0.25 Hz finds the largest peak within
465..585 Hz; sine/cosine/DC least-squares refinement stays within 1 Hz of that peak.
The method does not fit around a presumed candidate frequency. Explained variance
must be at least 90%, and at least three complete cycles must be usable. Internal
short regions and boundary fits fail rather than trigger a new window or search.

The reference must stay within 0.5% of the earlier 500.65 Hz lead. Independent stereo
onsets must agree within 2 ms, and the full loop must stay near 2.4 seconds. Six
channel/threshold comparisons must agree in frequency direction, retain the loop
within 5 ms, and match `2^(1/12)` within 0.2% to support the one-semitone hypothesis.
An upward shift of another size remains a separate result. Failed or unclear audio
reports remain retained without refitting after data.

All 40 affected checks pass, including independent 44.1/48 kHz synthetic frequencies
500.65/530.42/557 Hz, exact wave recovery, mask preservation, source guards, conflicting
channels, wrong reference/loop, noise and changed-method rejection. Production code
is unchanged; the last full regression suite passed 853 tests.

- [Pair and frequency preregistration](../experiments/sound3-generated-pitch13-14-registration-001.json)
- [Reference software validation](../experiments/edited-sound3-pitch13-reference-001/software-validation.json)
- [Candidate software validation](../experiments/edited-sound3-pitch14-001/software-validation.json)
- [Physical endpoint results](sound3-tone-pitch-range-results.md)

After independent decoding into each leg's `derived/analysis-001/capture.symbols.npz`:

```text
python -m scripts.check_generated_sound3_pitch_restore --leg reference
python -m scripts.sound3_pitch_frequency_analysis --leg reference
```

The candidate uses `--leg candidate` only after reference validation. With both exact
native recaptures and audio reports, run
`python -m scripts.check_generated_sound3_pitch_frequency`.
Software reports remain hardware-unverified; physical acceptance and user observations
are recorded separately.

## Reference accepted; next physical action: candidate14

The generated13 reference is now physically accepted. Its entire 815-packet backup
matches the target body `7f09d45808d5a9064139b43f717bbc8bd8e99a9248411bc534641ff343783fdd`.
All nonpitch bits, volume36, sample data, keys, globals and other patterns are exact.
The user reports "done, and confirmed I can hear the pattern", without a subjective
interval or numeric display reading.

The 11.97-second ordinary playback is usable: all six frozen measurements pass at
approximately 500.626 Hz with full-loop intervals near 2.3998 seconds. All reference
lead, stereo onset, tone-fit and clipping checks pass without changing the method.
Backup peaks approximately 0.152/0.147 remain suitable at the established level.
All 31 content hashes and complete native reconstruction pass for the current genuine
read-only export: `experiments/exported-sound3-pitch13-reference-001/project.json`.

- [Separate reference hardware observation](../experiments/edited-sound3-pitch13-reference-001/hardware-observation-001.json)
- [Frozen reference measurements](../experiments/edited-sound3-pitch13-reference-001/pitch-frequency-results-001.json)
- [Reference-to-candidate handoff validation](../experiments/pitch13-reference-to-pitch14-workflow-validation-001.json)

Both prepared WAVs and artifacts retain their registered hashes. Candidate14
reception and frequency direction/interval remain pending. No pitch setter or
all-code law is inferred from the accepted reference.

1. Restore `experiments/edited-sound3-pitch14-001/restore.wav` with the established
   stereo path and playback level. Keep both knobs and all audio settings unchanged.
2. Select Pattern1 / Sound3 / TONE, stopped with write off.
3. Before playback, save a full backup as
   `experiments/edited-sound3-pitch14-001/capture.wav`, at the established reduced
   recording level with one second trailing silence.
4. Separately record 12–15 seconds of ordinary Pattern1 playback as
   `experiments/edited-sound3-pitch14-001/playback.wav`, then stop/write off.
5. Confirm restore success and audible pattern playback. No remembered pitch
   comparison or numeric display reading is required. Leave both knobs untouched.

## Completed interval control

Candidate14 reception is exact. All six frozen comparisons measure approximately
99.53 cents above reference13, supporting the preregistered one-semitone hypothesis
with stable loop timing. Volume36 and all unrelated state remain unchanged. The user
confirms pattern playback without a subjective interval claim. See
[results](generated-sound3-pitch-interval-results.md), the new bounded
[raw pitch edit](sound3-pitch-edits.md), and the next
[FILTER selection control](sound3-filter-probe-control.md).
