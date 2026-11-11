# First swing maximum control

Use the accepted 137 BPM state. No restore is needed. Keep **Pattern 1 / Sound 8 / TONE**,
stopped and write off. Leave knob B, all samples, patterns and other settings unchanged.

1. **Hold BPM continuously and turn only knob A fully clockwise** to maximum swing.
   Note any swing display value or label. Stop moving A before releasing BPM, then leave
   both knobs unchanged.
2. Read tempo without pressing BPM. It should remain **137 BPM**.
3. **Before playback or auditioning**, record a complete stereo backup at the established
   reduced levels with one second trailing silence as
   **experiments/event-037-b-swing-maximum/capture.wav**.
4. Report the swing display value/label, or **no swing value shown**, and whether tempo
   stayed 137. Leave the new swing setting in place.

The [official guide](https://teenage.engineering/guides/po-33/en), section 6, specifies
BPM+A for swing. No percentage, display scale or maximum encoded value is assumed.

The preregistered location lead is second `0x7d5c` payload byte 130, immediately after
tempo. It currently contains 0. The hypothesis is that only this byte changes; numeric
units are unknown. Both global records are pinned before collection. All raw differences
remain visible without fitting a new offset or encoding. An unchanged backup remains
eligible as an already-at-maximum or no-serialized-change outcome.

Core checks require valid native data, pinned baseline, unchanged samples/patterns/
selectors and unchanged 137 tempo. Location and direct display-value equality are separate
hypotheses. Missing display numbers are never filled in from bytes; even one direct match
does not establish the swing scale. No swing writer is enabled. Tempo editing still
rejects a changed non-tempo global context until suitable evidence exists.

- [Registration](../experiments/event-037-b-swing-maximum/swing-registration.json)
- Baseline 137 body: `5f25b5efd909c93b0aa0cdbb31d8aff170ea5edeb9ca6dd48eb2d7778ae696cb`
- After decoding at threshold 0.0063:
  `python -m scripts.check_swing_max_control --display-value ACTUAL_SWING_VALUE --display-text ACTUAL_LABEL`
- With no numeric display, omit `--display-value` and preserve the report with `--display-text`.

## Completed

The user reportedS18 and only the registered adjacent byte changes0 to18. Serialized
tempo137 and every other field remain exact. See [results](swing-max18-results.md).
The next [range series](swing-range-series-control.md) keeps the minimum unknown,
observes an intermediate9 and returns to the complete S18 state.
