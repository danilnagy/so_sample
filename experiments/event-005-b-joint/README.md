# Combined Step 1 + Step 2 control

Only one new recording is requested. Pattern 1 should contain the recognizable kick
from Sound 9, slice 1 at both Steps 1 and 2, with no other event changes.

The last hardware capture had the Step 1 kick. If that is still the current state,
leave Step 1 in place and add the same kick at Step 2. Before recording, exit write
mode and keep playback stopped. Keep sound/slice selection, tempo, effects, knobs,
pattern sequence and the validated reduced recording level unchanged. Record the
full stereo dump here as capture.wav. No fresh A or A-return is required. Leave this
two-kick state unchanged afterward, so a consecutive repeat remains possible if needed.

If the current state has changed since the last capture, state the changes along with
the recording; do not silently treat a different starting state as the planned control.
The existing empty, Step 1 and Step 2 recordings are reused explicitly.

Prediction report: ../joint-predictions-001.json. Its fixed model predictions are hashed
before the combined capture. No model, alignment or endpoint is adjusted afterward to
rescue a prediction. Comparison uses raw labels, staggered phases and phase increments
under XOR and modulo-four additive hypotheses. A failure rejects those specific views;
it does not prove encryption or rule out all possible coding.
