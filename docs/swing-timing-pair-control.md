# Generated swing timing pair

Two research WAVs share one controlled pattern change: copy the complete opaque
Pattern 1 Step 13 row to the empty Step 2 using the existing bounded `clone_step`.
This adds Sound 3/key 16 on an offbeat while preserving every existing event and
all samples. The repeated tone now occurs at both Steps 2 and 13 with identical note
parameters and sample data.

The straight target sets second `0x7d5c` payload byte 130 to 0. The second target sets
that byte to 6, a previously unobserved interior value. The two targets differ in
exactly one plain payload byte; their patterns and all other bytes are identical.
Tempo stays 137. Both strict phase round trips, complete native-body recovery and
packet recovery pass. Software validation remains hardware-unverified.

| Leg | Folder | Target native-body SHA-256 |
| --- | --- | --- |
| First, straight | `experiments/edited-swing-timing0-001` | `1da3b29b71a0ce601b485b94a5b40256058d3cf79f61d50f743d25fe28aa03e2` |
| Later, swing 6 | `experiments/edited-swing-timing6-001` | `fc595d91e0eff23869c4236bc9c602745c8e6de63c9d5257b9ba3152e9678175` |

## First physical action

1. Restore the complete `experiments/edited-swing-timing0-001/restore.wav` using the
   established stereo playback path and level.
2. Keep both knobs untouched. Select Pattern 1 / Sound 8 / TONE, stopped and write off.
3. Before playing the pattern, record a complete backup as
   `experiments/edited-swing-timing0-001/capture.wav`, at the established reduced levels
   with one second of trailing silence.
4. Make a **separate ordinary-audio recording** of Pattern 1 playing for 8–10 seconds.
   Save `experiments/edited-swing-timing0-001/playback.wav`, then stop playback. Keep
   recording and output settings consistent for the later comparison; avoid clipping.
5. Report restore success and whether you hear the added note immediately after
   the first beat. Leave Pattern 1 / Sound 8 / TONE stopped and write off.

Do not turn A to read swing: doing so would change the restored value. The complete
backup will independently verify the stored byte and added event. The second restore
waits until the straight control is checked; its files are already prepared.

## Registered timing hypotheses

Repeated note onsets at Steps 2 and 13 identify the same sound and pitch, reducing
attack differences. At zero swing the gaps alternate 11 and 5 sixteenth steps. The
nominal full-pattern duration at 137 BPM is approximately 1.752 seconds.

Compared with straight playback, a working positive swing value should increase the
Step 13→Step 2 gap and decrease the Step 2→Step 13 gap while retaining the whole loop
period. Measure repeated onset gaps using the common repeated-tone component. Report
measured changes without assuming percentage or clock units. Require at least three
resolvable complete cycles; unclear audio leaves timing unevaluated.

All 40 affected swing/tempo tests pass, including actual range captures, source guards,
exact offbeat placement, isolated pair differences and rejection of wrong recaptured
pitch or other global changes. No public swing writer is enabled.

- [Pair registration](../experiments/swing-timing-pair-registration-001.json)
- [Straight software validation](../experiments/edited-swing-timing0-001/software-validation.json)
- [Swing-6 software validation](../experiments/edited-swing-timing6-001/software-validation.json)
- Prepare: `python -m scripts.prepare_swing_timing_pair` (fresh outputs only)
- After independent backup decoding: `python -m scripts.check_swing_timing_recapture --swing 0`

Native recapture results and later ordinary-audio measurements remain separate from
immutable user observations. Neither software compilation nor successful decoding
alone establishes the audible timing effect.

## Straight control completed; next swing-6 action

The first restore, exact native backup, added-note user confirmation and ordinary
timing all pass. See [results](swing-straight-control-results.md). The repeated component
is near 500 Hz, correcting the original high-note description. That original immutable
registration is retained; a separate fixed measurement method is registered before
target data. All 47 affected tests pass.

1. Restore `experiments/edited-swing-timing6-001/restore.wav` using the same stereo path
   and playback level. Keep both knobs untouched.
2. Select Pattern 1 / Sound 8 / TONE, stopped and write off. Before pattern playback,
   record `experiments/edited-swing-timing6-001/capture.wav` at the established levels
   with one second trailing silence.
3. Separately record at least 10 seconds of ordinary Pattern 1 playback as
   `experiments/edited-swing-timing6-001/playback.wav`, keeping the same audio settings.
   Then stop and return to Pattern 1 / Sound 8 / TONE, write off.
4. Report restore success and whether the offbeat rhythm sounds different. A subjective
   change is not required for the measurement: raw recapture and timing will be checked
   independently. Leave both knobs untouched, including when checking swing.

Analysis after independent native decoding:

```text
python -m scripts.check_swing_timing_recapture --swing 6
python -m scripts.swing_timing_analysis experiments/edited-swing-timing6-001/playback.wav --out experiments/edited-swing-timing6-001/playback-timing-results-001.json
python -m scripts.check_swing_timing_pair_audio
```

The fixed comparison requires all six channel/threshold results to show a short-gap
increase and long-gap decrease exceeding 3 ms, with loop drift and unbalanced gap
changes each at most 3 ms. Missing or inconsistent audio remains unevaluated. No timing
units are fitted to the candidate value.

Completed: the user hears more swing, the entire swing-6 native target recaptures
exactly, and all six frozen stereo timing comparisons pass. See
[results](generated-swing6-results.md). The approximately 27 ms measured delay does
not yet assign timer or percentage units. Public bounded swing plans replay both
accepted WAVs byte-for-byte; the next action is the
[joint tempo/swing composition test](joint-tempo-swing-control.md).
