# Reconstruction: candidate 002 accepted by hardware

## Hardware finding

The user reports that candidate 001 failed to restore using the same procedure as their
working baselines. An original baseline was retried immediately afterward and restored
successfully. The first candidate is recorded as rejected in
`experiments/baseline-002/generated-restore-44100-001.json`; its WAV and reports are preserved.
That controlled result directs investigation toward synthesis rather than the playback path.
Candidate 001's software equality remains a valid observation, but not evidence of hardware
acceptance. Both our decoder and the upstream decoder discard the second sign pair of each
cycle, so an incorrect inter-symbol waveform can evade both checks.

## Measured correction

The failed phase-blend-0.1 encoder used a 7800 Hz carrier and a whole-phase crossfade over
cycle fractions 0.6?0.9. The original terminal carrier is approximately 7812 Hz in short
noisy sinusoid-fit windows; 7812.5 Hz is the new nominal synthesis choice, not an exact
measurement of the device clock. The decoder's nominal 7800 Hz sign-run quantization remains
unchanged to preserve established artifacts and reference comparisons.

More substantially, the captured transition waveform behaves like staggered quadrature
components. The first pair of quarter-center signs gives the current label; the third
quarter depends on the following label's high coordinate, and the fourth on the current
label's low coordinate. The discarded sign pair therefore constrains the physical waveform.
This relation is a measured waveform model, not a confirmed protocol-bit or state format.

For carrier-cycle coordinate t, high-sign a and low-sign b in {-1,+1}, the model is:

```text
I(t) = a[floor(t + 0.625)] * cos(2*pi*(t - 0.125))
Q(t) = b[floor(t - 0.125)] * cos(2*pi*(t - 0.375))
wave(t) = amplitude * (I(t) + Q(t)) / sqrt(2)
```

The I coordinate changes at fraction 0.375 to the next label's high sign; Q changes at
fraction 0.125 to the current label's low sign. These changes occur at each component's
zero crossing, so they preserve waveform continuity. Indexes are clamped only for explicit
first/final hold behavior. We do not substitute a guessed payload or musical state.

## Independent waveform evidence

The comparison uses the same fixed cycle window [30,500) in each capture, with its origin
at the recorded acquisition crossing plus one nominal quarter cycle. It does not search
for a favorable shift or discard mismatching spans. Correlation is scale-independent;
a fitted gain is recorded separately to quantify residuals.

| Capture | Legacy shape at 7812.5 Hz, left / right | Corrected shape at 7812.5 Hz, left / right |
| --- | ---: | ---: |
| 001 | 0.594 / 0.599 | 0.978 / 0.979 |
| 002 | 0.593 / 0.599 | 0.977 / 0.979 |
| 003 | 0.592 / 0.591 | 0.970 / 0.969 |

Changing frequency alone leaves the poor transition match. The staggered model substantially
improves it on both development capture 002 and the independently recorded captures 001/003.
The original 7800 Hz model performs even worse over these fixed windows due to accumulated
carrier phase mismatch. Full metrics, source hashes and terminal carrier-fit windows are in
[the waveform audit](../experiments/reconstruction-waveform-audit.json). These short-window
results do not prove exact global timing, a clock-tolerance range or hardware acceptance.

## Candidate to test

Primary corrected file:
`experiments/baseline-002/derived/roundtrip-44100-002/restore.wav`

- Encoder: staggered-quadrature-0.2; carrier 7812.5 Hz.
- Format: 44.1 kHz, signed 16-bit stereo, amplitude 0.5.
- Duration: 252.407120 seconds (~4:12).
- SHA-256: 778e05040b81ee451bb0692b9765181c4a7ad30fb49904495bccc048ef4232f7.
- Source: capture 002, decoded at explicit threshold 0.02.

The 48 kHz software-test counterpart is in `roundtrip-48000-002/restore.wav`, SHA-256
05825e13e1d3bd06a9e38f9bb7754143727671698a8641f29d411e6fd3c0c3ae.
Use the primary file first so the sample rate matches the accepted original recording.

Both rates re-decode to exactly 1,970,367 labels per channel: no changes, unequal tails,
shifts or dropped symbols. The unchanged upstream converter agrees over its retained
985,182 interleaved complete bytes; our full-symbol comparison preserves the three terminal
labels per channel that upstream's complete-byte layout omits. Its agreement is recorded
for reproducibility and is not the independent physical-waveform validation.

96 tests pass. These include all phase transitions and endpoints at both rates, analytical
constant-phase values, a hand-derived quarter-center sequence that the rejected model
cannot reproduce, continuity at component updates, invalid parameters, safe outputs,
polarity/clock perturbations, genuine roundtrips and comparisons against all three actual
recordings. Ruff lint and format checks pass. Original WAV hashes remain unchanged.

## Boundary policies and limits

The half-cycle acquisition primer (one low quarter then one high quarter), full final
stored cycle, half-cycle final-phase hold guard, and 100 ms silence at each end are unchanged
from candidate 001. No extra long carrier preamble is added. This makes the tested correction
specific to carrier timing and transition synthesis. Original pre-acquisition samples/noise
are not reconstructed; primer and guard are explicit software conventions awaiting hardware
validation. Every stored complete phase label remains represented.

The encoder rejects empty/unequal channels, initial labels other than 2 or 3, and explicitly
recorded incomplete final-cycle signs. It does not infer missing symbols. Reports always
state hardware_verified=false until separate manual evidence is recorded.

## Commands

```powershell
.\.venv\Scripts\python.exe -m po33_re roundtrip experiments/baseline-002/capture.wav --threshold 0.02 --carrier-hz 7812.5 --sample-rate 44100 --out-dir experiments/baseline-002/derived/your-new-run
.\.venv\Scripts\python.exe -m po33_re encode experiments/baseline-002/derived/threshold-002/capture.symbols.npz --out restore.wav --report encode.json --carrier-hz 7812.5
```

The default encoder carrier is now 7812.5 Hz; --carrier-hz records an explicit experiment.
The valid diagnostic range is 7600-8000 Hz; it is not a claim about supported device tolerance.
Roundtrip compares complete labels and exact counts, without alignment, returning exit 3
on equality failure. Input errors return 2, and unsafe output aliases/overwrites are rejected.

## Manual test and handoff

Keep a known-good backup; restoration replaces current samples and patterns. Use the same
working stereo playback setup and level, with processing disabled, and restore candidate
002. No playback or hardware actions are automated by the toolkit.

Record accepted/rejected/inconclusive, any device display, and whether populated samples,
drum slices, patterns and settings match. If accepted, make an untouched backup as
`experiments/reconstructed-001/capture.wav` and retain a second copy. Log controls changed
during checks because they may themselves be serialized. Candidate 002's manual record is
`experiments/baseline-002/generated-restore-44100-002.json`; it now records accepted
based on the user's successful restore report. A successful receive indication alone is weaker evidence than matching musical
behavior and a re-capture. Hardware completion of Session 3 remains pending.

## Hardware acceptance update

The user reports that the corrected 44.1 kHz candidate restored successfully. This is
local hardware acceptance evidence for the specific WAV with SHA-256
778e05040b81ee451bb0692b9765181c4a7ad30fb49904495bccc048ef4232f7. The previous candidate
remains rejected. Acceptance is not generalized to all encoder inputs or the untested
48 kHz candidate. Automated encode and roundtrip reports remain hardware_verified=false;
manual evidence is stored separately. Detailed behavioral checks, a fresh backup and
analysis of that re-capture are still needed to complete repeated reconstruction validation.

## Post-restore backup result

The new backup was inspected, but its phase-symbol content differs substantially from the original after a matching opening region. An amplitude-scaled threshold restores matching counts but not equality. See [post-restore validation](../experiments/reconstructed-001/validation.md). Hardware receive acceptance remains recorded; unchanged musical state and repeated content preservation are not yet established.

## Controlled hardware roundtrip validated

The user restored corrected candidate 002 and immediately backed up without intervening
state changes. The lower-level re-capture matches all 1,970,367 labels per channel and
their exact counts against baseline 002/003, with zero alignment or discarded labels.
See [controlled re-capture validation](../experiments/reconstructed-002/validation.md).
This is evidence for this local device/state/playback path; it does not verify arbitrary
state editing or every encoder input. The current recording level is suitable when using
the explicit 0.0063 threshold profile.
