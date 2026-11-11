# Public FILTER plan returns high-pass52 to center63

The current device state is the accepted generated high-pass52 body. A public
`set_sound3_filter` plan changes its 16 Sound3/Pattern1 cells to raw63, preserving
pitch14, volume36 and every unrelated bit. The target exactly reconstructs the
whole independent recorded center body and every packet. Software WAV recovery
passes; generated63 reception and listening remain pending.

1. Restore `experiments/edited-sound3-filter63-center-001/restore.wav` with the
   established stereo setup and playback level. Keep both knobs and audio
   settings unchanged.
2. Before ordinary playback, save a complete backup as
   `experiments/edited-sound3-filter63-center-001/capture.wav` at the established
   reduced recording level with one second trailing silence.
3. Select Pattern1 / Sound3 / FILTER without moving either knob. Play with write
   off, report whether the whole sample sounds unfiltered again, then stop.

No WRITE-held pass or separate playback.wav is needed. Do not move A to center to
force an audible result: this control tests the stored plan. The expected body is
`8f80a398ac7130f1802ba865985cb3f7174f9f0129af1182eb6d5da450d6a341`.
Matching field63 alone is insufficient if another byte changes. A listening pass
does not prove broadband bypass or a complete filter law.

- [Preregistration and source/target identities](../experiments/sound3-generated-filter63-center-registration-001.json)
- [Public plan](../experiments/edited-sound3-filter63-center-001/plan.json)
- [Software compile report](../experiments/edited-sound3-filter63-center-001/compile-report.json)
- [Checker](../scripts/check_generated_sound3_filter_center_restore.py)
- [Public operation and scope](sound3-filter-edits.md)

After independent threshold-0.0063 decoding, run
`python -m scripts.check_generated_sound3_filter_center_restore`. Reports remain
hardware-unverified and immutable; physical and user evidence are separate.
The full production regression run passes1,025 tests; eight additional center
checker tests pass with no later production changes.

## Completed

The public-plan63 restore recaptures the entire predicted independent center body
and every packet. Pitch14, volume36 and all unrelated state remain exact. The user
confirms the sample sounds unfiltered. See [results](generated-sound3-filter63-results.md)
and the [next B probe](sound3-filter-B-probe-control.md). Original registration and
compiler reports remain unchanged and hardware-unverified.
