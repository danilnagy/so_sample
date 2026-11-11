# First tempo storage control

Use the current verified state after the imported sample was removed. No restore is
needed. The next experiment changes only the BPM preset through one short button press.

1. Keep **Pattern 1 / Sound 8 / TONE**, playback stopped and write off. Leave both knobs,
   sound parameters, swing, patterns and other settings unchanged.
2. Note the BPM currently shown on the display. **Tap BPM once**, without holding the
   button or turning either knob. Note the new BPM displayed.
3. Before playing or auditioning anything, record a complete stereo backup at the
   established reduced levels, including one second of trailing silence. Save it as
   **experiments/event-030-b-tempo-preset-once/capture.wav**.
4. Report both displayed numbers with the capture, for example **120 to 140**. This is
   an example, not an assumption about the current display. Leave the new tempo in place.

The [official guide](https://teenage.engineering/guides/po-33/en), section6, describes
the BPM button's 80, 120 and 140 presets. Holding BPM with a knob adjusts swing or fine
tempo, so those actions are excluded. Reviewed 2026-10-09.

The preregistered lead is payload byte129 (zero-based) of the second `0x7d5c` packet.
It currently contains120 within an otherwise mostly-zero prefix. The hypothesis is
that this single byte stores the displayed integer BPM directly. This numeric
coincidence is not a field identification, and the current displayed BPM is unknown
until supplied by the user. No offset or encoding will be refitted to rescue the test.

Core checks verify native integrity, the pinned baseline, all sample records, all
patterns and selector order. Independent hypotheses report whether any bytes change,
whether changes stay within the opaque global packets, whether only byte129 changes,
and whether its before/after values match the independently observed display values.
An identical backup remains a valid no-serialized-change outcome. Additional changes,
wrong offsets and unsupported direct-byte matches remain visible. Without both display
observations, the numeric hypothesis remains unevaluated.

No tempo writer is enabled from this first control. Confirmation across independent
values and a return control will precede any writable-field decision.

- [Tempo registration](../experiments/event-030-b-tempo-preset-once/tempo-registration.json)
- Baseline body SHA-256: `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0`
- After decoding at threshold 0.0063:
  `python -m scripts.check_tempo_control --before-bpm OBSERVED_BEFORE --after-bpm OBSERVED_AFTER`

## Completed

The user independently reported120 to140, and only the registered byte changes with
every sample, pattern and unrelated byte preserved. See
[results](tempo-120-to140-results.md). The next
[third-value and return series](tempo-preset-series-control.md) collects80 then120.
The field remains unavailable for writing until appropriate restore evidence exists.
