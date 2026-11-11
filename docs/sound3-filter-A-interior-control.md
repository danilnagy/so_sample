# Two FILTER interiors and exact center return

The device is currently at the audible center, with a single middle tick and raw
63 in all 16 Sound 3 / Pattern 1 cells. This new registration follows the observed
center failure of both earlier scalar-order hypotheses. It does not replace that
failure. We now test two branches with a possible special neutral code, without
predicting exact interior values or uniformity.

Keep Pattern 1 / Sound 3 / FILTER selected, B and audio settings unchanged. For
each pass, start playback, hold WRITE while moving only A over about 5 seconds,
then hold WRITE another 3 seconds with the knobs stationary. Release WRITE, stop
playback, ensure write is off, and save a full backup before the next pass.

1. From center, turn A counterclockwise to about halfway between center and fully
   counterclockwise: roughly one-quarter of the knob's total travel. Save
   `experiments/event-059-f-sound3-filter-A-lowpass-interior/capture.wav`.
2. Turn A clockwise to about halfway between center and fully clockwise: roughly
   three-quarters of total travel. Save
   `experiments/event-060-g-sound3-filter-A-highpass-interior/capture.wav`.
3. Return A to the single middle tick where the whole sample sounds unfiltered.
   Save `experiments/event-061-h-return-sound3-filter-A-center/capture.wav`.

Use the established reduced recording level and one second trailing silence.
Report the actual sound/display changes at each position; quiet or inaudible
interiors are acceptable. Keep the chosen position rather than adjusting it to
chase an audible result. Do not press keyboard keys or hold BPM/FX during the
passes. No restore or separate playback recording is required. Leave A at center
and B untouched.

The contiguous scalar-branch hypothesis predicts interior low-pass codes strictly
between 1 and 32, and high-pass codes strictly between 31 and 62. The alternate
grouping predicts respective strict intervals 4–32 and 31–59. Both are new,
falsifiable hypotheses registered before interior data. They are not already
decoded mode bits. Ramps, unchanged data and broader third-byte changes are retained
literally; failures will not widen the masks or bounds.

All other state, including pitch 14 and volume 36, must remain exact under the
strict masks. The final return predicts the entire independent center body
`8f80a398ac7130f1802ba865985cb3f7174f9f0129af1182eb6d5da450d6a341`
and every packet. Matching raw 63 values alone cannot satisfy that prediction.
UI numbers, Hz scaling, full field width, resonance and a public writer remain
unknown. This set does not make new quantitative audio predictions.

- [Preregistration](../experiments/sound3-filter-A-interior-registration-001.json)
- [Completed center results and display correction](sound3-filter-A-center-results.md)
- [Checker](../scripts/check_sound3_filter_interior.py)

After independently decoding all three backups at threshold 0.0063, run
`python -m scripts.check_sound3_filter_interior`. Software reports remain
hardware-unverified. All 69 affected checks pass; production code is unchanged,
with 917 tests passing in the last full regression run.

## Completed

Recorded low-pass is contiguous 16 / alternate 1, high-pass is 52 / 19, and the
63 / 63 return exactly matches the entire independent center body and all packets.
Only strict candidate bits change; pitch 14, volume 36 and all unrelated state
remain exact. The user confirms LPF, HPF and no-filter behavior. Both contiguous
branch-order predictions pass; both alternate branch predictions fail and remain
retained. See [results](sound3-filter-A-interior-results.md) and the
[next generated low-pass restore](generated-sound3-filter-pair-control.md).
