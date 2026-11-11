# Low-pass16 reference with B0, then B63 candidate

The current genuine state is the exact B0 minimum return at cutoff63, pitch14 and
volume36. Both new research targets set known low-pass cutoff16. Their difference
is confined to third-primary bits2..7: reference0 versus candidate63. All other
state stays exact. These are new combined contexts, not replays of independently
recorded whole bodies. Both 44.1kHz stereo PCM16 WAVs pass full phase/native recovery.

## Next action: reference only

1. Restore `experiments/edited-sound3-filter16-B0-reference-001/restore.wav` using
   the established stereo setup and playback level. Keep both knobs and recording
   settings unchanged.
2. Before ordinary playback, save a complete backup as
   `experiments/edited-sound3-filter16-B0-reference-001/capture.wav` at the established
   reduced level with one second trailing silence.
3. Select Pattern1 / Sound3 / FILTER without moving either knob. Separately record
   12–15 seconds of ordinary Pattern1 playback as
   `experiments/edited-sound3-filter16-B0-reference-001/playback.wav`, then stop and
   ensure write is off. Report whether restore succeeded and whether the filtered
   pattern is recognizable; quiet or unexpected results should be reported as heard.

No WRITE-held pass is needed. This reference must have exact native reception and
usable fixed-method audio before the candidate is requested. Its expected entire
body is `ae37ebfdfd485e0e20313c4faeb26065132375c7f0194681fffeda837c6b6264`.

## Later candidate after the reference is verified

The prepared second WAV is
`experiments/edited-sound3-filter16-B63-candidate-001/restore.wav`, targeting
`fd0817c1c7791225eab3fe2f2d91f459ddad0c00fd0aacbd87e8672232323039`.
Its native and audio checkers require the first-leg hardware observation and
registered reference data. Do not request this restore until the reference gate
passes. It will use the same backup-before-playback and separate ordinary audio
sequence, with no knob movement.

Both playback recordings use the unchanged original common tone method: both
channels, three onset thresholds, a fixed80–180ms fit window and identical broad
frequency search. The reference frequency must be within0.5% of530.26Hz, the prior
measured pitch14 lead. That new reference gate is separate from the unused original
pitch13 lead stored in the shared method parameters; no method is fitted around
new resonance data.

The new audio hypothesis predicts candidate/reference repeated-component amplitude
at least1.05 in all six comparisons, with relative frequency difference at most0.5%
and loop difference at most5ms. This hypothesis was chosen after endpoint data and
before either new audio capture. Failure remains a failure. Too-quiet, distorted,
insufficient or otherwise unusable audio remains retained without changing windows,
thresholds or search ranges. A passing comparison concerns this repeated tone at
fixed cutoff16; it does not establish a broadband response or general resonance law.

- [Preregistration and frozen identities](../experiments/sound3-generated-filter16-B0-B63-registration-001.json)
- [Reference software validation](../experiments/edited-sound3-filter16-B0-reference-001/software-validation.json)
- [Candidate software validation](../experiments/edited-sound3-filter16-B63-candidate-001/software-validation.json)
- [Research constructor](../scripts/prepare_generated_sound3_resonance_pair.py)
- [Native checker](../scripts/check_generated_sound3_resonance_restore.py)
- [Frozen audio comparison](../scripts/sound3_resonance_audio.py)
- [Recorded endpoint results](sound3-filter-B-range-results.md)

After independent threshold0.0063 backup decoding, run
`python -m scripts.check_generated_sound3_resonance_restore --leg reference`, then
`python -m scripts.sound3_resonance_audio --leg reference`. The later second leg uses
`--leg candidate`. Reports are immutable and hardware-unverified. All108 affected
checks pass. Public cutoff guards and production code remain unchanged since the
full1,025-test run; no public resonance writer is enabled.

## Reference completed; candidate is now the next action

The reference recaptures the entire target and every packet. All six frozen audio
measurements are usable near530.28Hz with stable2.4002-second timing, and the user
confirms filtered-pattern playback. The10.96-second file is shorter than the
requested target but meets unchanged registered coverage. See
[reference results](generated-sound3-resonance-reference-results.md). Original
registration and generated targets remain unchanged.

1. Restore `experiments/edited-sound3-filter16-B63-candidate-001/restore.wav` using
   the established stereo setup and playback level, keeping both knobs and all
   recording settings unchanged.
2. Before ordinary playback, save the full backup as
   `experiments/edited-sound3-filter16-B63-candidate-001/capture.wav` at the
   established reduced level with one second trailing silence.
3. Select Pattern1 / Sound3 / FILTER without knob movement. Separately record12–15
   seconds of ordinary Pattern1 playback as
   `experiments/edited-sound3-filter16-B63-candidate-001/playback.wav`, then stop
   and ensure write is off. Report actual sound changes, including uncertainty.

No WRITE-held pass is needed. Do not adjust knobs or recording levels to force
an expected result. The entire target remains
`fd0817c1c7791225eab3fe2f2d91f459ddad0c00fd0aacbd87e8672232323039`.
Candidate reception and the registered amplitude hypothesis are still unverified.

## Both legs completed

The B63 target recaptures exactly and all six frozen component-amplitude increase
comparisons pass, with ratios around7.15 and consistent frequency/loop. The user
reports more resonance or filter effect. See [pair results](generated-sound3-resonance-pair-results.md)
and the [next B32 interior control](generated-sound3-resonance-middle-control.md).
Original registration, generated targets and software reports remain unchanged.
