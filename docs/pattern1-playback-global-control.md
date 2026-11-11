# Stopped repeat and ordinary playback

The corrected FX16 capture verifies the original clear prediction: Pattern1's
eight footer bytes return to FF and the entire independent pre-FX state returns
except second0x7d5c payload byte131. That byte is now7, rather than the original0.
It was9 after octave-up and1 after octave-down. Its role remains unknown.

This control separates another stopped backup from ordinary playback, with no FX
action, write pass or knob movement. Two new complete WAVs are required:

1. Keep Pattern1 selected, playback stopped and write off. Without playing first,
   save a new backup as
   `experiments/event-069-a-pattern1-stopped-repeat/capture.wav`.
2. After that backup, with write off, press PLAY, let Pattern1 run approximately
   five seconds, then press PLAY to stop. Leave FX and both knobs untouched. Save
   another new backup as
   `experiments/event-070-b-pattern1-plain-playback/capture.wav`.

Use the established reduced recording level, record the complete dump and keep
one second of trailing silence. No separate ordinary playback recording is needed.

Before data, the stopped-repeat hypothesis predicts the complete accepted clear
body unchanged. The playback hypothesis permits only global131 low-four changes;
whole-byte scope is a separate broader diagnostic. Every pattern byte including
the FF footer, all samples and every other global byte must remain exact. The
playback global value and whether it changes are explicitly unknown. Preserve
any failed hypothesis rather than revising its mask after seeing the result.

A playback-associated change would support a narrower explanation for the FX
co-occurrence. It would not establish a step counter, effect selector, nibble
order or public FX writer. An unchanged playback capture also remains useful;
it cannot rule out every possible transient role from a single stop position.

- [Frozen registration](../experiments/pattern1-playback-global-registration-001.json)
- [Preparation](../scripts/prepare_pattern1_playback_global_control.py)
- [Checker](../scripts/check_pattern1_playback_global_control.py)
- [Corrected clear evidence](pattern1-FX16-corrected-clear-control.md)

Decode both captures independently at threshold0.0063 into their respective
`derived/analysis-001` directories, then run
`python -m scripts.check_pattern1_playback_global_control`. The immutable output
remains hardware-unverified until separately bound to the physical observations.
The checker rejects a copied source or pair of identical raw WAVs; distinct WAVs
with identical native bodies are legitimate control results.

## Completed

Both independent captures preserve the entire pre-battery-change clear body,
including global131=7 and footerFF. The user reports replacing dead batteries
before recording the pair. The stopped-repeat prediction passes, but this
unchanged playback result does not determine the global role. See
[results and intervention limits](pattern1-plain-playback-results.md). The next
[fixed footer-only octave-up restore](generated-pattern1-FX-up-control.md) tests
the effect separately from the previously co-occurring global change.
