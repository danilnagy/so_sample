# Third tempo preset and exact original-state return

Use the current observed **140 BPM** state. No restore is needed. Keep
**Pattern 1 / Sound 8 / TONE**, stopped and write off, with both knobs and all other
settings unchanged throughout. Record each backup before playback or auditioning.

1. Tap **BPM once** and note the displayed value; the expected next preset is **80 BPM**.
   If it differs, report that value before continuing the second leg. Record a complete
   stereo backup at the established reduced levels with one second of trailing silence.
   Save it as **experiments/event-031-b-tempo-80/capture.wav**.
2. After saving the 80 backup, tap **BPM once** again and note the displayed value; the
   expected return is **120 BPM**. Record another complete backup with the same settings
   and trailing silence. Save it as
   **experiments/event-032-a-return-tempo-120/capture.wav**.
3. Leave the device at 120 BPM and report both actual transitions with the uploads.
   Expected observations are **140 to 80** and **80 to 120**; these are predictions until
   confirmed by the display.

The [official guide](https://teenage.engineering/guides/po-33/en), section6, describes
the BPM button presets 80, 120 and 140. Neither holding BPM nor turning a knob is needed.

Both legs are preregistered at the same fixed payload offset 129 in the second `0x7d5c`
packet. The direct-byte model predicts one change to 80, then one change to 120. The second
capture must also recover the **entire independent original 120 native body**, not merely
its tempo byte. Samples, patterns, selectors and all unrelated packets must remain exact.

The return transition is compared with the actual first capture, whose identity is
reported independently. Equality of that first capture to the predicted 80 body remains
a separate hypothesis; unexpected first data cannot silently redefine the prediction.
Display values are supplied by the user, never filled in from candidate bytes. Missing
observations, stale first captures, changed unrelated globals and incomplete returns do
not support the series. Raw differences remain visible without offset or encoding fitting.

The predictor is research-only and creates native comparison bodies, not restore audio.
No tempo writer is enabled, and the first physical association is not hardware validation
of a generated tempo edit. If this series passes, that generated restore is a later gate.

- [Series registration](../experiments/tempo-preset-series-registration-001.json)
- [Software prediction checks](../experiments/tempo-preset-series-prediction-checks-001.json)
- Predicted 80 body SHA-256: `2a1a594b027dcd228f20e2b72961e995b27a3c8378643d74ad03a323ce3c17ce`
- Expected 120 return body SHA-256: `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0`
- After decoding both captures at threshold 0.0063:
  `python -m scripts.check_tempo_preset_series --first-after-bpm OBSERVED_FIRST --return-after-bpm OBSERVED_RETURN`

## Completed

Both displays were independently confirmed, both captures match the fixed-byte model,
and the 120 return equals the complete independent original backup. See
[results](tempo-preset-series-results.md). The next
[generated restore](generated-tempo80-control.md) tests whether the device accepts the
same tempo change supplied through reconstructed backup audio.
