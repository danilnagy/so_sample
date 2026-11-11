# Unknown B maximum and exact minimum return

Current genuine B minimum has raw six-bit0 in all16 Sound3/Pattern1 cells, cutoff63,
pitch14 and volume36. The next two captures are registered before collection. The
maximum code and body remain unknown; the final return predicts the entire
independent minimum body and every packet.

Keep Pattern1 / Sound3 / FILTER selected, A and audio settings unchanged. For
each action, start playback, hold WRITE while moving only B over about5 seconds,
then hold WRITE3 more seconds stationary. Release WRITE, stop playback, ensure
write is off and save a full backup before proceeding.

1. Turn only B **fully clockwise**. Save
   `experiments/event-063-b-sound3-filter-B-lock-up/capture.wav`.
2. Return only B **fully counterclockwise**. Save
   `experiments/event-064-c-return-sound3-filter-B-lock-down/capture.wav`.

Use the established reduced recording level and one second trailing silence.
Report actual sound/display changes, including no change at the neutral cutoff.
Leave B at minimum and A untouched. Do not press keyboard keys or hold BPM/FX.
No restore or separate ordinary playback recording is required.

The return target is
`bee177abf44962fde6bee1279572df70c7f0b5cf87ffadc51ffaae4768d3d274`,
with both raw projections0 throughout. Matching field0 alone cannot rescue another
changed byte. Both0x7c and0xfc mask reports remain distinct, despite the original
narrow-mask failure. Broader FILTER snapshots and coupled A updates are retained;
they do not rescue strict six-bit support. Endpoint ramps are literal, with no
uniformity requirement or averaged values. No maximum63, numeric UI, audible
response, resonance law or full width is assumed.

- [Preregistration](../experiments/sound3-filter-B-range-registration-001.json)
- [Minimum results](sound3-filter-B-minimum-results.md)
- [Checker](../scripts/check_sound3_filter_B_range.py)

After independently decoding both captures at threshold0.0063, run
`python -m scripts.check_sound3_filter_B_range`. Reports are immutable and remain
hardware-unverified. All82 affected checks pass. Public cutoff guards remain
unchanged and reject the new B context; no resonance writer is enabled.
The last full production regression run passed1,025 tests.

## Completed

Maximum is six-bit63 / narrow31 in all16 cells. The return is0 under both projections
and matches the entire earlier independent minimum body and every packet. All
noncandidate state remains exact. The user reports no sound change and a resonance
display adjustment, without numeric endpoint readings. See
[results](sound3-filter-B-range-results.md) and the
[next filtered B0 reference](generated-sound3-resonance-pair-control.md).
