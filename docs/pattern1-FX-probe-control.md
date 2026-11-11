# Saved Pattern1 FX7 location probe

The current verified state is low-pass16/resonance32 at pitch14/volume36, with an
independent eight-byte FF Pattern1 footer. This probe registers that footer as a
new possible saved-effect location, without guessing the raw code or nibble order.

The [official PO-33 guide](https://teenage.engineering/guides/po-33/en), section6,
identifies FX key7 as octave-up and says that effects are saved while write mode
is enabled. This differs from holding WRITE during parameter-knob automation.

1. Keep Pattern1 selected, both knobs and all audio settings unchanged. Stop playback.
2. Press WRITE once to enable write mode; confirm its indicator is on.
3. Start playback. Hold **FX and key7 together** for about8 seconds, without moving
   either knob or pressing other keyboard keys. Do not hold WRITE during this pass.
4. Release FX/key7, immediately stop playback, then switch write mode off.
5. Save a complete backup as `experiments/event-065-a-pattern1-FX7-recorded/capture.wav`
   at the established reduced recording level, with one second trailing silence.
   Report the sound/display changes actually observed, including uncertainty.

No restore or separate playback recording is needed. Footer bytes1024..1031 are
only a location hypothesis; primary/auxiliary Pattern1 changes and other state
differences remain separate alternatives. Both low-first and high-first nibble
vectors are retained literally. Release timing may leave mixed values; no uniformity,
whole target body, zero-based code or exact value6 is predicted.

The source backup preceded already confirmed ordinary playback. This combined
control includes that playback plus enabling write and recording FX7; unrelated
differences are not automatically attributed solely to FX. No effect encoding
order, full effect map or public FX writer is promoted from a first capture.

- [Preregistration](../experiments/pattern1-FX7-probe-registration-001.json)
- [Checker](../scripts/check_pattern1_fx_probe.py)
- [Verified source](generated-sound3-resonance-middle-results.md)

After independent threshold0.0063 decoding, run
`python -m scripts.check_pattern1_fx_probe`. Reports stay immutable and
hardware-unverified. All42 affected FX/resonance checks pass after the full1,137-test
run, with no later production changes.

## Completed with a strict-model failure

The footer has uniform6 under both nibble orders, but global payload byte131 also
changes0 to9. Original footer-only preservation therefore fails and remains
retained. Notes, parameters, samples and every other payload byte stay exact.
The user confirms hearing an octave higher. See [results](pattern1-FX7-results.md)
and the [next FX8/clear controls](pattern1-FX8-clear-control.md).
