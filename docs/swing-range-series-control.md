# Swing minimum, displayed 9 and exact S18 return

Use the current observed **S18** state at 137 BPM. No restore is needed. Keep
**Pattern 1 / Sound 8 / TONE**, stopped and write off, with knob B and all other settings
unchanged. For every adjustment, hold BPM continuously while moving only knob A,
then stop moving A before releasing BPM. Record before playback and before the next leg.

1. Turn A **fully counterclockwise** to minimum swing. Note the actual display text,
   including any minus sign; the minimum number is deliberately unspecified.
   Save a complete stereo backup as
   **experiments/event-038-b-swing-minimum/capture.wav**.
2. Set the displayed swing number to **9**. Note its actual label/value and save
   **experiments/event-039-c-swing-9/capture.wav**.
3. Return to the maximum **S18** and save
   **experiments/event-040-a-return-swing18/capture.wav**.
4. Leave S18 in place and report all three exact display readings, including a minus
   sign if present. Tempo should stay 137. If 9 cannot be reached, report the available
   value before continuing. Use the same reduced recording levels and one second of
   trailing silence for each capture.

The [official guide](https://teenage.engineering/guides/po-33/en), section 6, specifies
BPM+A for swing. This series assumes neither a percentage scale nor a minimum value.

The fixed location remains second `0x7d5c` payload byte 130. Two numeric models are
registered before minimum data: displayed value equals the raw unsigned byte, or
equals signed8(raw), interpreting bytes>=128 as byte-256. Positive 18 alone cannot
distinguish those models. Any different scale remains an explicit failed outcome;
the checker will not fit a conversion afterward.

The middle 9 and return 18 complete-body predictions are pinned in advance. The return
must equal the entire independent original S18 body. Minimum has no guessed body/value.
Conditionally, if the user independently observes minimum 0, its complete body must
also equal the genuine zero-byte state captured before maximum swing. Each leg uses
the actual preceding capture, with unrelated global/sound-parameter/sample/pattern
preservation checked separately. Missing readings are never supplied from data bytes.

No swing writer is enabled, and units remain unconfirmed even if display/byte models
pass. The current pattern mainly has quarter-beat events; later audible swing validation
should use an offbeat event so timing can be checked independently of serialization.

- [Series registration](../experiments/swing-range-series-registration-001.json)
- Middle 9 body SHA-256: `ea13a17f3bb7e131ed8c54d3809bd66eeb298425b4f4d62324d1520ae801942b`
- Return 18 body SHA-256: `51b9358a087173aa4ebd4e49eda47e698ba34c7dd077237ccb7d353291b6eea8`
- Conditional minimum 0 body: `5f25b5efd909c93b0aa0cdbb31d8aff170ea5edeb9ca6dd48eb2d7778ae696cb`
- After decoding all captures at threshold 0.0063:
  `python -m scripts.check_swing_range_series --display-values ACTUAL_MIN ACTUAL_MIDDLE ACTUAL_RETURN`

Completed: the user independently reported S00, S09 and S18. Every control and full-body
prediction passes, including the zero-state and maximum-state returns. See
[results](swing-range-results.md) and the [next generated timing pair](swing-timing-pair-control.md).
