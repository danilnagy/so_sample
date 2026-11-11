# Audible FILTER center stores literal 63

The center backup independently decodes at threshold 0.0063 to 815 checksum-valid
packets and end byte 156758. All 16 Sound 3 / Pattern 1 candidate fields contain
63 under both bit groupings. Only the strict second-primary high-four and
third-primary low-two masks change; pitch 14, volume 36 and every other state bit
remain exact. Note tuples are `0ef983`; parameter-only tuples are `0ef903`.
The complete body is
`8f80a398ac7130f1802ba865985cb3f7174f9f0129af1182eb6d5da450d6a341`.

Both preregistered monotonic scalar-order hypotheses fail: center 63 is outside
the contiguous endpoint interval 1–62 and the alternative interval 4–59. Native
validity and scope checks pass independently. These failed predictions are retained
in the immutable report. A special neutral code is now a post-observation
hypothesis; it does not establish encoding order, field width or a complete law.

The user reports: "done, confirmed I could hear the whole sample as if neither
filter was applied. the indicator at bottom fills up at the start for both filters,
but in the middle it is single tick in middle". The prior full-bar midpoint cue
was incorrect. The user identified the audible center and supplied the single
middle tick cue. Original experiment instructions and registration are retained;
the correction is in the separate manual observation and status record.

All six frozen ordinary-audio comparisons pass. Repeated-component amplitude ratios
are 0.972773–0.973553 relative to the pinned prior playback, within the registered
5% tolerance. Frequency is approximately 530.2605–530.2613 Hz; relative changes are
below 0.002%, and loop differences are below 0.205 ms. This supports the registered
near-reference tone-component hypothesis with stable pitch and timing, alongside
the user's neutral-like listening report. Broadband bypass and a cutoff curve are
not demonstrated. No thresholds, windows or bounds were changed after collection.

Capture peaks are approximately 0.1468 and 0.1411 full scale with no clipping. The
established reduced recording level remains suitable. The current genuine read-only
export is `experiments/exported-sound3-filter-A-center-001/project.json`; all 31
content hashes and complete native reconstruction pass. Raw previews retain the
unchanged sample codes and do not render filter or pattern-pitch effects.

- [Native report, including failed scalar orders](../experiments/event-058-e-sound3-filter-A-center/center-native-results-001.json)
- [Frozen audio comparison](../experiments/event-058-e-sound3-filter-A-center/center-audio-comparison-results-001.json)
- [Hardware observation](../experiments/event-058-e-sound3-filter-A-center/hardware-observation-001.json)
- [User report and display correction](../experiments/event-058-e-sound3-filter-A-center/manual-observation.json)
- [Explicit post-observation literal-63 model](../experiments/sound3-filter-center63-post-observation-model-001.json)
- [Next interior controls and complete center return](sound3-filter-A-interior-control.md)

Software reports remain hardware-unverified and physical evidence stays separate.
All 69 affected FILTER/pitch checks pass; production code is unchanged since the
last full 917-test run. No public filter writer or resonance field is enabled.
