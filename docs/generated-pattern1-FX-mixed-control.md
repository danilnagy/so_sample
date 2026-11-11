# Mixed up/down blocks in Pattern1

The exact accepted clear body supplies the source. A new research restore changes
only the eight Pattern1 footer bytes to `6666666677777777`, leaving global131=7
and every sample, note and parameter byte exact. Both nibble-order projections
give eight raw6 values followed by eight raw7 values.

The new listening hypothesis is octave-up in steps1..8 and octave-down in
steps9..16, repeating each loop. This block association is a prediction, not a
conclusion from native body equality. The existing notes have different pitches,
so report what you hear, including uncertainty. Success would still not determine
which nibble belongs to the first step of an adjacent pair.

1. Restore `experiments/edited-pattern1-FX6-7-halves-global7-001/restore.wav` using
   the established stereo playback settings. Leave both knobs untouched.
2. With playback stopped and write off, record a complete `capture.wav` in that
   same folder **before playing**. Use the same reduced level and one second
   trailing silence.
3. With write off, play Pattern1 for several loops. Report whether it switches
   between higher and lower sections, then stop. Do not press FX or turn knobs.

No separate ordinary playback recording is needed. The mixed target is research
only: public uniform effect plans continue to reject mixed sources and targets.
The generated WAV passes strict phase and full native packet/body roundtrips.
Physical restore and the listening hypothesis remain pending.

- [Frozen prediction](../experiments/pattern1-generated-mixed-FX-halves-global7-registration-001.json)
- [Software validation](../experiments/edited-pattern1-FX6-7-halves-global7-001/software-validation.json)
- [Fixed constructor](../scripts/prepare_generated_pattern1_fx_mixed.py)
- [Recapture checker](../scripts/check_generated_pattern1_fx_mixed.py)
- [Uniform edit plans](pattern1-effect-edits.md)

After independently decoding the physical capture at threshold0.0063, run
`python -m scripts.check_generated_pattern1_fx_mixed`. Its immutable software
report requires the exact full target, with no global-byte masking. It does not
infer audible sequencing or nibble order from the backup bytes. Preserve any
failed native or listening prediction rather than widening its scope.

All1,246 regression tests pass after uniform-edit promotion, followed by72 focused
checks including the new mixed research test. No later production code changed.

## Completed

The capture matches every packet and the full target. The user confirms first
high then low. See [results](generated-pattern1-FX-mixed-results.md). Adjacent-step
nibble order remains unknown; the next
[F6/6F first-pair control](pattern1-FX-first-pair-control.md) registers both local
order alternatives and a fixed first-note audio comparison before new data.
