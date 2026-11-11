# Generated swing 6 accepted and measured

The user reported **“done, confirmed pattern does sound like it has more swing.”**
The physical restore accepts the new swing-6 target. Its complete independent backup
matches every generated packet and native byte, with 815 valid checksums ending at
byte 156758. Body SHA-256 is
`fc595d91e0eff23869c4236bc9c602745c8e6de63c9d5257b9ba3152e9678175`.
The serialized tempo is 137 and swing byte is 6. Samples, pattern events and all other
global bytes match the straight control exactly. No independent S06 display reading
was supplied or inferred.

The separate ordinary playback is 8.040 seconds long and supplies eight usable repeated
tone onsets, or three complete cycles. It satisfies the registered minimum despite
being shorter than the requested ten-second recording. Both channels pass all three
frozen envelope thresholds using the 500.65 Hz component selected from straight data.

| Median interval at 25% threshold, left channel | Straight | Swing 6 |
| --- | --- | --- |
| Step 13 to next Step 2 | 0.547778 s | 0.575034 s |
| Step 2 to Step 13 | 1.203946 s | 1.176961 s |
| Whole loop | 1.751723 s | 1.751995 s |

Across all six threshold/channel comparisons, the short gap increases by
27.19–27.30 ms and the long gap decreases by 26.93–27.04 ms. Whole-loop drift remains
below 0.30 ms. Every preregistered direction, loop-preservation and balanced-gap check
passes. This independently supports a working positive swing edit and agrees with
the user's audible observation. One measured positive value does not establish
percentage or timer units.

The immutable hardware observation binds raw capture/playback files, user confirmation,
decoded symbols, native results, timing results, frozen method and pair comparison.
Compiler and automated research reports remain hardware-unverified.

- [Hardware observation](../experiments/edited-swing-timing6-001/hardware-observation-001.json)
- [Native recapture](../experiments/edited-swing-timing6-001/hardware-recapture-results-001.json)
- [Timing comparison](../experiments/swing-timing-pair-audio-results-001.json)
- Current genuine export (`experiments/exported-swing-timing6-001/project.json`, a local research artifact, not in the repository)

All 31 export content hashes and complete native-body reconstruction pass. The guarded
public writer now supports integer swing values 0 to 18 within the recognized global
context. Physical 0/9/18 and generated 6 ground this range policy; every integer is not
individually hardware tested. See [swing edit plans](swing-edits.md).

The next [joint tempo/swing restore](joint-tempo-swing-control.md) tests the composition
of two supported edits without changing samples or patterns.
