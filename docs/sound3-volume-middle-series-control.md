# Recorded volume quarter, halfway and exact maximum return

The louder return is exact, but the minimum also cleared two adjacent bits, rejecting
the old four-bit-only prediction. The next three captures test interior positions
against separately declared six-bit and enable-flag alternatives.

No restore is needed. Keep **Pattern 1 / Sound 3 / TONE**, tempo 100, swing 9 and knob A
untouched. For each pass, play Pattern 1, hold **WRITE**, and slowly move only B to the
specified position over about **5 seconds**. Hold WRITE **3 more seconds** with both
knobs stationary; release WRITE, stop playback and ensure write is off, then capture.
This uses the [official guide's](https://teenage.engineering/guides/po-33/en) section 6
parameter-locking procedure. Do not hold BPM/FX or press keyboard keys during the pass.

1. Set B to approximately **one-quarter of its full travel clockwise from minimum**.
   This is a mechanical position, not a requested displayed number or gain percentage.
   Save `experiments/event-047-d-sound3-volume-lock-quarter/capture.wav`.
2. Set B approximately **halfway between its two physical stops**.
   Save `experiments/event-048-e-sound3-volume-lock-middle/capture.wav`.
3. Return B **fully clockwise** to maximum.
   Save `experiments/event-049-b-return-sound3-volume-lock-maximum/capture.wav`.
4. Report relative loudness at all three positions and any display labels/numbers
   you saw. Leave maximum recorded, Sound 3 / TONE selected, stopped and write off.

Save each before the next pass. Use the same reduced capture levels and one second
trailing silence. No separate ordinary playback recording is required for this series.

## Frozen alternative models

Only Pattern 1 Sound 3's first-byte `0xc0` and second-byte `0x0f` masks may change.
Every other primary bit, auxiliary byte, sound, sample, global setting and other pattern
must remain exact. The final complete body must recover independent maximum
`e34fbe7f6238c230deeacd96139b26e5ca88bb5f300a7831da87a24e32afaef7`.

The declared value orderings are:

- Contiguous little-endian six-bit value: `((byte0 >> 6) & 3) | ((byte1 & 15) << 2)`.
- First-byte pair as most significant: `((byte0 >> 6) << 4) | (byte1 & 15)`.
- Four-bit value `byte1 & 15`, with first-byte pair `0xc0` at nonzero values and zero
  at zero values as a possible enable/disable alternative.

Both value orderings are evaluated for uniform fields and strict minimum < quarter <
middle < maximum order. Auxiliary raw position bands are 10–22 at quarter and 26–38 at
halfway. These are deliberately separate from field-scope/order support: approximate
mechanical positions are not a calibrated gain or UI scale, and cannot alone prove
bit ordering. No exact interior value or complete body is guessed. Mixed ramp values,
unexpected masks or ambiguous alternatives remain explicit results.

The older failed minimum result remains immutable and separately pinned in the new
registration. No six-bit packed order, gain curve or public volume writer is declared
verified by software alone.

- [New registration](../experiments/sound3-volume-middle-series-registration-001.json)
- [Failed four-bit model and exact return](sound3-volume-lock-range-results.md)
- After independent decoding at threshold 0.0063:
  `python -m scripts.check_sound3_volume_middle_series`
- Optional `--display-texts` records three actual user-provided labels; absent readings
  are never inferred from bytes.

All 13 affected tests pass, including the real failed minimum, both synthetic orderings,
unresolved enable alternatives, mixed/nonuniform values and strict mask preservation.

Completed: all field-scope and whole-return checks pass. Quarter is uniform21 under
both orderings; middle retains several levels and fails the original uniformity/band
condition. The simple enable-pair alternative is refuted. See
[results](sound3-volume-middle-series-results.md). The next
[generated gain-ordering pair](generated-sound3-volume18-control.md) uses the genuine
uniform quarter as reference, without rewriting the failed middle result.
