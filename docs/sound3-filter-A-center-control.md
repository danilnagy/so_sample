# Recorded FILTER A center and ordinary playback

The current device state is the exact clockwise return, with contiguous projection
62, pitch 14 and volume 36. This control registers the next interior capture before
collection. It does not guess an exact center code or require uniform values.

Keep Pattern 1 / Sound 3 / FILTER selected, B and all audio settings unchanged.

1. Start playback, hold WRITE, and move only A counterclockwise from maximum toward
   the midpoint over about 5 seconds. Stop where the bottom bar is full and the
   sample sounds clearest. Hold WRITE for 3 more seconds with the knobs stationary;
   release WRITE, stop playback and ensure write is off.
2. **Before ordinary playback**, save a complete backup at the established reduced
   recording level, with one second trailing silence, as
   `experiments/event-058-e-sound3-filter-A-center/capture.wav`.
3. Separately record 12–15 seconds of ordinary Pattern 1 playback as
   `experiments/event-058-e-sound3-filter-A-center/playback.wav`, then stop. Report
   whether the sample is audible and the bar is full, including any uncertainty.
   Leave A at this position and B untouched.

No restore is needed. Do not press keyboard keys or hold BPM/FX during the recorded
pass. The backup precedes ordinary playback so that its stored state can be checked
independently of any subsequent playback changes.

The native checker retains the strict candidate mask, broader alternatives, pitch
and volume checks, all literal values and any ramps. It tests two monotonic scalar
hypotheses separately: contiguous interior values strictly between 1 and 62, or
alternate values strictly between 4 and 59. Failure is retained and does not rule
out other mode or flag interpretations. Passing is not proof of a complete encoding.

The ordinary-audio comparison pins the existing accepted pitch-14 playback from
before recorded FILTER A. It reuses the original common frequency method unchanged:
both channels, all three onset thresholds and the fixed 80–180 ms fit window. The
registered near-reference component-amplitude hypothesis allows 5% relative
difference, with frequency within 0.5% and loop difference within 5 ms. This is a
comparison at the repeated tone component, not proof of broadband bypass. The old
reference audio was already observed; this new comparison is registered before
center data. No new thresholds or windows will be fitted to rescue a failure.

The acoustic result is separate from the stored-state result. A positive combined
claim also requires valid native scope and an actual stored candidate change.
No resonance field, cutoff law, numeric UI code or public filter writer is inferred.

- [Preregistration](../experiments/sound3-filter-A-center-registration-001.json)
- [Completed endpoint results](sound3-filter-A-range-results.md)
- [Native checker](../scripts/check_sound3_filter_center.py)
- [Frozen audio comparison](../scripts/sound3_filter_center_audio.py)

After independently decoding the complete backup at threshold 0.0063, run
`python -m scripts.check_sound3_filter_center`, then
`python -m scripts.sound3_filter_center_audio`. Each writes fresh immutable reports;
all software reports remain hardware-unverified. All 53 affected checks pass, with
no production changes since the last full 917-test regression run.

## Completed with a display correction and failed scalar orders

The audible center has uniform literal 63 under both projections, with all strict
scope, pitch and volume checks passing. Both numerical between-endpoint hypotheses
fail, while all six frozen near-reference tone-component comparisons pass. The
user confirms the whole sample sounds unfiltered and corrects the display cue:
**center is a single middle tick**, not the full bar originally requested above.
Original instructions and preregistration remain unchanged; the correction and
failures are separate evidence. See [results](sound3-filter-A-center-results.md)
and the [next interior controls](sound3-filter-A-interior-control.md).
