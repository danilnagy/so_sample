# Independent waveform clock, round 5

A new amplitude-derived clock and direct quarter-point sign sampler agree with the
existing decoder throughout the tested interiors of five genuine captures, on both
channels. All four quarter positions agree with the accepted staggered encoder model.
This strengthens modulation evidence but does not establish payload framing or state
fields. Production decoding/encoding and original WAVs remain unchanged.

## Independent clock derivation

For equal-magnitude orthogonal components, write
`x = A/sqrt(2) * (I*cos(theta) + Q*sin(theta))`, where I and Q are signs.
Then `x^2 = A^2/2 * (1 + I*Q*sin(2*theta))` and
`(x^2-A^2/2)^2 = A^4/8 * (1-cos(4*theta))`.
The fourth harmonic is independent of I and Q. With the encoder's carrier origin
`theta=2*pi*(t-0.125)`, its signed harmonic coefficient gives phase `8*pi*t`.

The probe estimates squared-amplitude DC and fits constant/cosine/sine coefficients
in 500-frame windows using the nominal 7812.5 Hz carrier. It unwraps harmonic phase
and interpolates the resulting quarter clock. Mixing a sampled tone above Nyquist
uses its sampled alias; no above-Nyquist waveform reconstruction is assumed.
The fitted tone-to-standard-deviation diagnostic is not a probability or a guaranteed
clock quality measure. Unequal components, noise, filtering and rapid clock drift can
violate the model or affect its estimate.

The clock uses no zero-crossing times, sign-run counts or artifact label values.
Amplitude start/end bounds are reused from each artifact explicitly. Four quarter
offsets and 128 whole-label start positions are compared using only the first 2048
sampled pilot labels to resolve acquisition ambiguity. A unique perfect candidate
was found for each channel. The remainder is compared without changing that choice.
Incomplete edge clock windows are excluded, with exact spans in each report; acquisition
and untested endpoint samples remain outside this independent validation.

## Genuine-capture results

Reports ../experiments/waveform-probes-001.json through 005 correspond to empty event-002-a,
Step 1, Step 2, Step 3 and repeated Step 1. Each pins source and artifact hashes.

| Capture | Checked reference-label span, both channels | Label disagreements | All four quarter disagreements |
| --- | --- | --- | --- |
| Empty | [43,1970285) | 0 | 0 |
| Step 1 | [43,1970274) | 0 | 0 |
| Step 2 | [44,1970261) | 0 | 0 |
| Step 3 | [44,1970240) | 0 | 0 |
| Step 1 repeat | [43,1970258) | 0 | 0 |

Quarter validation checks one fewer label per span, because it requires the following
high coordinate. Expected quartet is `[high[n], low[n], NOT high[n+1], NOT low[n]]`.
No disagreement was observed at any quarter position. Thus the quarter positions omitted
from the label artifact are redundant under this model in the tested interiors. This
does not mean arbitrary signals or all device states satisfy that relationship.

The dense changed spans from previous rounds are supported by a clock derived from raw
amplitude, not just by variants of the same crossing counter. No extra independent
component bit lane emerged here. State coding and serialization remain unresolved.

## Next hardware control

One combined-state backup is now needed: Pattern 1 contains the same Sound 9, slice 1
kick at both Steps 1 and 2. Existing controls have empty, Step 1-only and Step 2-only
states. The current last-recorded state is Step 1-only; add only Step 2 if unchanged.
Use ../experiments/event-005-b-joint/capture.wav and preserve the validated recording level.
Detailed user actions and control limits are in that folder's README.md.

Before the new capture, fixed predictions were registered in
../experiments/joint-predictions-001.json. For each channel and raw-label/staggered-phase/
staggered-increment view, test `joint = empty XOR step1 XOR step2` and
`joint = (step1+step2-empty) mod 4`. Prediction arrays and all source artifacts are hashed.
This tests specific affine behavior under two presumed independent musical-state edits;
UI serialization or interactions may confound it. Failure does not exclude every linear
code, and agreement alone does not establish writable fields or a safe edited restore.
The already failed exact Step 3 onset prediction is not revised.

No fresh A or A-return is requested for this focused test. Leave the combined state
unchanged afterward so a consecutive repeat can be recorded if unexpected differences
require a control. Any changes since the last Step 1 recording must be reported.

## Reproduction

```powershell
.\.venv\Scripts\python.exe scripts/waveform_probes.py experiments/event-002-a/capture.wav experiments/event-002-a/derived/analysis-001/capture.symbols.npz --out experiments/waveform-new.json
.\.venv\Scripts\python.exe scripts/joint_probes.py experiments/event-002-a/derived/analysis-001/capture.symbols.npz experiments/event-001-b/derived/analysis-001/capture.symbols.npz experiments/event-002-b/derived/analysis-001/capture.symbols.npz --joint experiments/event-005-b-joint/derived/analysis-001/capture.symbols.npz --registration experiments/joint-predictions-001.json --out experiments/joint-results-001.json
```

The second command is for the future capture after decoding it at the established
normalized threshold 0.0063. It requires original artifact hashes and prediction hashes
to match the preregistration. No shift, fitting, coordinate remapping or endpoint correction
is performed to rescue any prediction. Unequal lengths are reported alongside shared
content, rather than silently padded or called fully equal.

Five focused tests pass: independent analytic amplitude carriers at both recording rates
with carrier frequency offset, invalid waveform checks, hand-specified affine predictions
with unequal endpoints, and a nonlinear counterexample. These supplement earlier tests.

The complete regression suite passed: 134 tests in 40.76 seconds. Ruff lint and formatting
pass for src/tests/scripts. The actual preregistration/comparison command was also exercised
with a known wrong joint state (Step 1-only): all 12 prediction hashes were verified and
all 12 shared-span predictions failed, as expected. That negative-control report is ignored
under .tools/joint-probe-negative-control.json, not registered as a hardware experiment.
