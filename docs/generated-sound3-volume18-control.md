# Uniform recorded reference and generated volume-ordering probe

Two software-verified restore WAVs are prepared from the genuine uniform quarter
capture. The first exactly replays its complete native body, with raw code21 common
to both proposed orderings. The second changes only the candidate masks in all16
Sound 3 cells to contiguous code18, which the alternative ordering interprets as36.
All samples, note-key bytes, other primary bits, globals and other patterns remain exact.

| Leg | Folder | Native target SHA-256 |
| --- | --- | --- |
| First, genuine reference replay | `experiments/replayed-sound3-volume21-reference-001` | `937b33f0c2be408e8f2321e3dabb146b2ae74976ed9ded6ddec3a3214cdd13e4` |
| Later, generated18 candidate | `experiments/edited-sound3-volume18-001` | `f9a66a8a6f50e47cdf04ec325f8f265b676d079e60646f290a96e83603d52a7c` |

Both WAVs pass strict phase and complete body/packet round trips. Their software reports
remain hardware-unverified. The recorded middle ramp is retained as nonuniform; this
test does not repeat or rewrite that experiment.

## First physical action: reference

1. Restore `experiments/replayed-sound3-volume21-reference-001/restore.wav` using the
   established stereo path and playback level.
2. Keep both knobs and audio settings unchanged. Select Pattern 1 / Sound 3 / TONE,
   stopped and write off. Do not turn B to read a volume display.
3. Before playing the pattern, save a complete backup as
   `experiments/replayed-sound3-volume21-reference-001/capture.wav` at established reduced
   levels with one second trailing silence.
4. Separately record **12–15 seconds of ordinary Pattern 1 playback** as
   `experiments/replayed-sound3-volume21-reference-001/playback.wav`, then stop/write off.
5. Confirm restore success and that the phrase is recognizable. Leave both knobs
   untouched. The next candidate waits until reference reception and usable audio
   are checked; its files are already prepared.

## Frozen gain test

The contiguous model predicts generated18 quieter than reference21; the alternative
model predicts generated36 louder than reference21. No exact amplitude ratio, linear
curve, dB scale or UI number is assumed. Six independent channel/envelope-threshold
comparisons must agree in direction with at least3 complete cycles, stable pitch and
the unchanged2.4-second loop. A3% relative amplitude margin prevents tiny noise changes
being called a directional result.

The prior repeated Sound 3/key16 component near500.65 Hz is a fixed lead. The gain method
uses a ±15 Hz band, three relative envelope thresholds and steady sine fits80–180 ms
after onset. Pitch differences must remain below0.5%, loop differences below5 ms and
fit explained variance at least90%. These settings are registered before **both** pair
audio captures. No candidate-data-driven frequency or window rescue is permitted.
The absolute method can be inconclusive if the reference is unusable; dependent
candidate work waits for clarification. Ordinary mix RMS is not used as Sound 3 gain.

No public volume writer is enabled. Only the exact independently captured quarter
body can feed the research constructor; the target is fixed18. All15 affected tests
pass, including mask preservation, source guards, independent44.1/48 kHz sine-amplitude
measurement, opposite gain directions and rejection of changed pitch/tempo or thresholds.

- [Pair registration](../experiments/sound3-generated-volume18-pair-registration-001.json)
- [Gain-method registration](../experiments/sound3-volume18-gain-method-registration-001.json)
- [Reference software validation](../experiments/replayed-sound3-volume21-reference-001/software-validation.json)
- [Candidate software validation](../experiments/edited-sound3-volume18-001/software-validation.json)

After independent native decoding of reference:

```text
python -m scripts.check_generated_sound3_volume18_restore --leg reference
python -m scripts.sound3_volume_gain_analysis experiments/replayed-sound3-volume21-reference-001/playback.wav --out experiments/replayed-sound3-volume21-reference-001/playback-gain-results-001.json
```

Candidate reception uses `--leg candidate`, with the same ordinary-audio measurement
method. Once both legs have exact native recaptures and audio reports:
`python -m scripts.check_generated_sound3_volume18_gain`.
User confirmation and hardware acceptance are separate immutable observations; no
software report is promoted to hardware verification.

## Reference accepted; next physical action: generated candidate

The reference is now hardware verified. Its full 815-packet body exactly matches
the registered uniform21 target. The user reports: "done and confirmed it sounds
like the lower volume". Separate 21.27-second ordinary playback passes all six
frozen channel/threshold measurements, with the repeated tone near500.57 Hz and
the loop near2.40043 seconds. Neither knob position nor a numeric volume display
is inferred. Backup peaks near0.161/0.155 remain suitable at the established level.

The [hardware observation](../experiments/replayed-sound3-volume21-reference-001/hardware-observation-001.json)
binds the complete native check, original playback, unchanged gain method and user
report. All31 content hashes and full-body reconstruction pass for the current
genuine read-only export:
`experiments/exported-sound3-volume21-reference-001/project.json`.
Sample previews preserve raw data and do not render pattern gain.

Both prepared WAVs retain their registered hashes. The candidate remains untested;
the [handoff validation](../experiments/volume21-reference-to-candidate-workflow-validation-001.json)
records that reference reception and usable audio passed before candidate data.
The orderings, gain direction and public volume editing remain unresolved.

1. Restore `experiments/edited-sound3-volume18-001/restore.wav` with the established
   stereo path and playback level. Keep both knobs and all audio settings unchanged.
2. Select Pattern1 / Sound3 / TONE with playback stopped and write off.
3. Before playing, save a complete backup as
   `experiments/edited-sound3-volume18-001/capture.wav` with the established reduced
   recording level and one second of trailing silence.
4. Separately record12–15 seconds of ordinary Pattern1 playback as
   `experiments/edited-sound3-volume18-001/playback.wav`, then stop/write off.
5. Report successful restore, the same recognizable phrase, and whether Sound3 is
   quieter, louder or about the same as the reference. Leave both knobs untouched.

Only after native reception and independent audio checks can the registered opposite
gain predictions be evaluated. No software report is changed to hardware verified.

## Completed pair

Both native recaptures and all frozen audio comparisons now pass. Generated18 has
about18.1% lower repeated-tone amplitude than uniform21 with stable pitch and loop,
supporting contiguous ordering. The user's uncertain louder guess is retained as
uncertain, not counted as directional confirmation. See
[results](generated-sound3-volume18-results.md) and the next
[complementary upper-interior control](generated-sound3-volume36-control.md).
No public volume writer or exact gain law is enabled.
