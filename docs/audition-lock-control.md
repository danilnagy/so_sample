# Audition-lock observation: do auditions follow a pattern's locks?

A backup holds no base knob settings ([knobs](sound-knobs-results.md),
[live volume](sound3-live-volume-results.md)). Every note the web app writes carries
full parameter locks, so a restored pattern plays as designed, but a sound auditioned by
hand plays at whatever the device holds. After restoring an app-built project the person
heard auditions as if the filter were closed, and reported that playing the pattern once
did not change that. This observation measures it.

## Restore

Built by the web app's own compiler, `web/scripts/build-audition-lock-restore.ts`, from
the verified empty template: Sound 16 key 1 holds a 200 Hz sawtooth hit with 55
harmonics (0.27 s), and Pattern 1 plays it on steps 1, 5, 9 and 13 with the app's
default locks on each note: pitch 13, volume 36, filter 63 (the bypass), resonance 1.
Tempo 120, chain of Pattern 1 alone. The registration pins the restore, its decoded
target, the build script and the method script.

## Session

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_audition_lock_observation
.\.venv\Scripts\python.exe -m po33_re hw run experiments/observe-audition-locks-001
.\.venv\Scripts\python.exe -m scripts.check_audition_lock_observation
.\.venv\Scripts\python.exe -m scripts.finalize_audition_lock_observation
```

The session restores, records the backup and checks it against the target, then arms
one 32-second playback recording and shows the procedure at that prompt. With Sound 16
selected and the knobs untouched:

1. Press key 1 four times, about one second apart: the auditions before.
2. Three seconds of silence, then PLAY; let Pattern 1 play twice; PLAY to stop.
3. Three seconds of silence, then key 1 four times again: the auditions after.

## Method

`scripts/audition_lock_method.py`, frozen and hashed in the registration. Hits are
envelope onsets at least 300 ms apart; groups split at gaps over two seconds. Each hit's
harmonics 1 to 50 are measured in a 60 to 220 ms window and expressed in dB against the
median of the pattern's hits, which are the bypass by construction. A group is low-pass,
high-pass, flat or silent as in the [filter law](filter-law-control.md), with 3 dB
margins; two groups match when both band means agree within 3 dB.

## Outcomes, registered before the session

- **audition_follows_last_lock**: the auditions before differ from the pattern and the
  auditions after match it. Playing a pattern would then set the live values.
- **audition_keeps_live_state**: the auditions before and after match each other and
  both differ from the pattern. Playing a pattern leaves the live values alone.
- **indistinguishable**: all three groups match; the live filter already was the bypass.
  A rerun with the filter knob turned fully counterclockwise before the auditions is
  then planned.
- **other**: anything else, with the reason in the measurements.

**Prediction: audition_keeps_live_state**, from the person's informal report. The
measurements also record which filter type the auditions showed before the pattern, as
an exploratory reading of the device's state after a restore.

## First session, 2026-11-08

The restore went through and the second backup attempt is exact by the web app's
decoder (the harness decoder stopped at the first packet, as it has no preamble search;
the first attempt was recorded far too quietly). The playback held the pattern alone:
the procedure had been shown at the restore step, so PLAY ran for the whole recording.
That recording is kept. The procedure now appears at the playback prompt, and the
three-part recording is taken again without a new restore:

```
.venv/bin/python -m scripts.prepare_audition_lock_retake
.venv/bin/python -m po33_re hw playback experiments/observe-audition-locks-001/retake-001 --seconds 32
.venv/bin/python -m scripts.check_audition_lock_observation
.venv/bin/python -m scripts.finalize_audition_lock_observation
```

Because the pattern has played once already, the retake's "before" auditions come after
a pattern play. If they differ from the pattern the registered outcomes apply as they
are. If they match it, the retake cannot separate "locks were followed" from "the live
setting was the bypass all along", and a rerun with the filter knob turned fully
counterclockwise before the auditions follows.

## Retake-001, 2026-11-08: the auditions by hand made no sound

The attempt that followed the procedure (`retake-001/attempts/playback-01.wav`, which
the recorder rejected for a late first sound) is silent for 8.3 s where the four presses
and the pause were due, holds two pattern passes, and is silent again for 17.5 s where
the presses after were due; the stretches sit at the noise floor, 70 dB under the
pattern's hits. The accepted attempt holds the pattern alone, since the recorder wants
a sound within 4.5 s and the presses gave none. The registered method found two hit
groups, not three, so the outcome is **other** and the prediction did not hold as
registered; the result and both recordings are kept.

Exploratory reading, not part of the registered method: after the restore, and still
after the pattern had played, pressing the drum key by hand produced no output at all.
The device's live setting for the sound is not merely filtered but inaudible, and
playing the pattern did not change it.

## Retake-002: the volume knob raised first

The device still holds the restored state. Before the recording the person selects
Sound 16 and turns knob B fully clockwise (the knob test showed B as volume), checks
that key 1 is audible, then follows the three-part procedure. The pattern's notes carry
volume 36 locks, so the question becomes measurable as level: auditions after the
pattern either stay as loud as the ones before (live state kept) or drop to the
pattern's level (locks followed). The method, outcomes and prediction are unchanged;
the amended procedure is recorded in `retake-002/experiment.json` before the recording.

```
.venv/bin/python -m po33_re hw playback experiments/observe-audition-locks-001/retake-002 --seconds 32
.venv/bin/python -m scripts.check_audition_lock_observation
.venv/bin/python -m scripts.finalize_audition_lock_observation
```

## Retake-002, 2026-11-08: audible after knob B, and the live level stays

With knob B turned fully clockwise, key 1 became audible. The attempt that followed the
procedure (`retake-002/attempts/playback-01.wav`, flagged by the recorder for a peak near
full scale) holds four presses, two pattern passes and five presses, then PLAY was
pressed again until the end, so the registered method found four hit groups, not three,
and the registered outcome stays **other**.

Exploratory, with the same measure over the first three groups alone: the presses before
and after the pattern are identical to each other (RMS 0.367 each, harmonic responses
alike to 0.01 dB) and both differ from the pattern's hits (RMS 0.253, top band 3.2 dB
apart), which gives **audition_keeps_live_state**, the predicted outcome. Playing the
pattern, whose notes carry volume 36 locks, left the sound's live level where the knob
had put it.

Taken together: a restore leaves a sound's live level inaudible, playing the pattern
does not touch the live level, and turning knob B sets it. A clean three-part take
without a trailing PLAY would turn the exploratory reading into a registered outcome;
until then the registered result is "other" and the prediction is counted as not held.

- [Results](audition-lock-results.md)
- [Registration](../experiments/audition-lock-registration-001.json)
- [Result](../experiments/audition-lock-result-001.json)
- [Observation](../experiments/observe-audition-locks-001/hardware-observation-001.json)
