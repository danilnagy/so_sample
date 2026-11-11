# Fine-tempo endpoints and exact 100 BPM return

Use the current physically observed **100 BPM** state. No restore is needed. Keep
**Pattern 1 / Sound 8 / TONE**, playback stopped and write off. Leave knob A and all
samples, patterns and other settings unchanged throughout.

For each target, **hold BPM continuously while turning only knob B**, stop moving B
before releasing BPM, then save that capture before changing tempo again. Do not move
either knob with BPM released. The [official guide](https://teenage.engineering/guides/po-33/en),
section 6, documents the fine-tempo range 60 to 240 through BPM+B; BPM+A changes swing.

1. Set the display to **60 BPM**. Record a complete stereo backup at the established
   reduced levels, with one second of trailing silence, as
   **experiments/event-034-b-fine-tempo-60/capture.wav**.
2. After saving it, set the display to **240 BPM**. Record another complete backup as
   **experiments/event-035-c-fine-tempo-240/capture.wav**.
3. After saving it, set the display back to **100 BPM**. Record the return backup as
   **experiments/event-036-a-return-fine-tempo-100/capture.wav**.
4. Leave the device at 100 BPM and report the three actual display values with the files.
   If an endpoint differs from the requested value, report the actual number before
   continuing the next leg. No playback or audition is needed for this series.

All three fixed-byte predictions are registered before collection. Each leg should
change only second `0x7d5c` payload byte 129 to the displayed integer value. The final
return must equal the **complete independently captured original 100 body**, including
every unrelated global and sound-parameter byte. Correct tempo alone cannot hide an
incomplete return.

Each comparison uses the actual preceding capture and separately checks it against
the preregistered expected body. Display readings are never inferred from candidate
bytes. Missing/extra captures or display readings, stale first states, sample corruption
and additional global changes do not support the series. Differences remain visible
without offset or encoding fitting.

The predictor is research-only and creates comparison bodies, not restore WAVs. Public
tempo scope remains the three tested presets. A successful endpoint/return series
will still leave generated fine-tempo restoration as a later hardware gate.

- [Series registration](../experiments/fine-tempo-range-series-registration-001.json)
- [Software prediction checks](../experiments/fine-tempo-range-series-prediction-checks-001.json)
- Predicted 60 body SHA-256: `8146205d12593b62c9b88c8ab9ad13603d10e409d84bef4a89e339ce96865f64`
- Predicted 240 body SHA-256: `681d3d77d3e557e7e345dde3928dc41bb62bc3c80b5f958dfd0857d678c68869`
- Expected 100 return SHA-256: `d01d2cdd2f9cd85aca19e17ebc7967327aba647926faf91dcb2db0fe42de2633`
- After decoding all three captures at threshold 0.0063:
  `python -m scripts.check_fine_tempo_range_series --display-bpms ACTUAL_MIN ACTUAL_MAX ACTUAL_RETURN`

## Completed

The displays were independently confirmed60,240,100. All captures match their fixed-byte
predictions, and the return equals the complete independent original100 backup. See
[results](fine-tempo-range-series-results.md). The next
[generated137 restore](generated-fine-tempo137-control.md) tests an unobserved fine
value without broadening the public writer in advance.
