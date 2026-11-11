# Fine tempo 80 to 100 control

Use the current hardware-verified **80 BPM** state. No restore is needed. The goal is
to check whether a non-preset fine tempo uses the same direct BPM byte as the presets.

1. Keep **Pattern 1 / Sound 8 / TONE**, playback stopped and write off. Note the displayed
   starting 80 BPM. Leave knob A and all samples/patterns/settings unchanged.
2. **Hold BPM continuously and turn only knob B** until the display reads **100 BPM**.
   Stop moving B before releasing BPM. Do not turn either knob afterward. This follows
   the [official guide](https://teenage.engineering/guides/po-33/en), section 6: BPM+B
   adjusts fine tempo; BPM+A adjusts swing and is excluded from this control.
3. **Before playback or auditioning**, record a complete stereo backup at the established
   reduced levels, including one second of trailing silence. Save it as
   **experiments/event-033-b-fine-tempo-100/capture.wav**.
4. Report the actual displayed BPM before and after, and leave the fine tempo in place.
   If 100 cannot be reached exactly, report the actual displayed value instead of guessing.

The preregistered direct-byte prediction changes only offset129 of the second `0x7d5c`
payload from 80 to 100. The complete expected body is saved before capture. Samples,
patterns and unrelated packets should remain exact. Other global changes or a different
byte encoding remain visible and may reject the single-byte model. The physical knob B
position necessarily changes; the test checks whether moving it with BPM held leaves
sample parameters unchanged.

This is an observational control, not a generated 100 restore. The public preset writer
still permits only 80/120/140 and rejects a fine-tempo 100 source or target. The documented
fine-tempo range is a lead for future controls, not a validated writable range.

- [Control registration](../experiments/event-033-b-fine-tempo-100/tempo-registration.json)
- [Software prediction checks](../experiments/fine-tempo100-prediction-validation-001.json)
- Expected 100 body SHA-256: `d01d2cdd2f9cd85aca19e17ebc7967327aba647926faf91dcb2db0fe42de2633`
- After decoding at threshold 0.0063:
  `python -m scripts.check_tempo_control --experiment-dir experiments/event-033-b-fine-tempo-100 --before-bpm OBSERVED_BEFORE --after-bpm OBSERVED_AFTER`

## Completed

The user reported100, and only the same tempo byte changes with every other serialized
field preserved. The entire body matches its prediction. See
[results](fine-tempo100-results.md). The next
[endpoint and return series](fine-tempo-range-series-control.md) requests60,240 and100
before any general fine-tempo writer is introduced.
