# First-pair effect order and the single-tone baseline

## First-pair outcome: exact reception, inconclusive audio

Both [first-pair restores](pattern1-FX-first-pair-control.md) were received exactly.
Each complete backup matches its target body and every packet. Only the Pattern 1
footer differs between the two, and global byte 131 stays 7. The person reported
completing all four recordings without a listening comparison.

The frozen first-tone comparison is **inconclusive**. No frequency ratio could be
formed, so neither nibble-order model is supported.

| Restore | Footer byte | First tone under the frozen method |
| --- | --- | --- |
| A | F6 | Usable in all six measurements, about 1190.65 Hz |
| B | 6F | Unusable: weak, decaying first sound near 1567.5 Hz, fit explained variance 0.068 |

The method forbids retuning or switching to a later note, so the comparison is kept
unchanged. See the [comparison](../experiments/pattern1-FX-first-pair-audio-comparison-001.json)
and the [B observation](../experiments/edited-pattern1-FX-6F-first-pair-001/hardware-observation-001.json).

## Single-tone measurement baseline

The next registered control reduces Pattern 1 to its one existing Sound 3 trigger on
step 1, with every other cell empty and all effects clear. It tests whether the
unchanged frozen method finds a usable first tone. It does not retune the method or
decide the effect order. See the
[registration](../experiments/pattern1-single-tone-FX-order-baseline-registration-001.json).

The restore is now hardware verified. The complete backup matches the registered
target body and every packet. All nine registered native checks pass:
- only Pattern 1 data changed, and the single-tone pattern is exact
- the Sound 3 step 1 cell is preserved
- all effects are clear, and global byte 131 stays 7

The audio check passes in all six measurements, both channels at three thresholds.

| Measure | Value |
| --- | --- |
| First tone | 1190.417 Hz in every measurement |
| Fit explained variance | 1.000 |
| Onset | 1.2405 s after recording start |
| Repeated tones (supplementary) | 6 tones, 2.40 s apart: one per loop at 100 BPM |

The one-tone-per-loop count was measured after the data arrived and is not part of the
frozen method. The person reported that the restore and playback worked, but gave no
explicit listening answer. See the
[hardware observation](../experiments/edited-pattern1-single-tone-no-FX-001/hardware-observation-001.json).
The current genuine read-only export is
`experiments/exported-pattern1-single-tone-no-FX-001/project.json`, with all export
hashes and the complete native body checked.

## A lead, not a result

Restore A's first tone, about 1190.65 Hz, lies within 0.02% of this unshifted
reference. In footer byte F6 the low nibble is 6 (octave up) and the high nibble is F
(no effect). An unshifted first step fits the high-nibble-first order. This was not
registered and does not settle the order: restore A also had other sounds on step 1,
and restore B's first sound is not an octave from the reference. A new effect-order
pair built on this single-tone pattern is now possible, since native reception and
audio usability both pass.

## How the round trip ran

This was the first experiment run through the [guided hardware session](hardware-sessions.md).
The first attempts failed for reasons in the computer setup, not in the device or the
restore file:

1. With both cables connected, the interface sent the PO-33 output back into its
   input. Backups carried a 4.5 ms delayed copy at strength 0.23 and failed to decode,
   and the first restore did not land.
2. The harness stopped playback before its last buffer played, which cut the final
   packet. The PO-33 showed ERR at the end, while the same file restored from Windows.
3. The first playback recording started its first tone 20 s late, and the level rose
   about 4 times partway through. It was set aside unevaluated.

The harness now detects feedback echoes, prompts for cable changes, pads playback with
silence, and rejects playback recordings that break the audio protocol. Every failed
attempt is kept in the experiment's `attempts/` folder with its analysis. Backup 3 also
recorded a change of global byte 131 from 7 to 1 after the failed restore, with no
saved pattern change. Its role remains unknown.
