# Complementary generated volume control accepted

The generated 36 restore recaptures its entire target body exactly:
`c0cc91737d5998aa5d6a214b1eeae0a46213b524d3f5fd307745d1bb780bd39c`.
All 815 packet checksums pass. Every sample, global byte, other pattern, other sound,
auxiliary key and bit outside the Sound 3 volume masks remains unchanged. The user
reports: "done, yes the pattern still plays". This confirms playback, without a
subjective gain-direction or numeric display claim.

The separate 21.12-second recording passes the original frozen measurement method.
All six channel/threshold comparisons measure repeated-tone amplitude between
2.203536 and 2.203639 times the uniform 21 reference. Frequency differs by at most
0.0182%, and the full loop by at most 0.443 ms, within the registered tolerances.
The contiguous 36>21 increase prediction passes; the alternate 9<21 decrease
prediction does not. No measurement parameters were adjusted after these recordings.

Together with the independently accepted generated 18 decrease, this supports the
contiguous six-bit volume interpretation in the tested Sound 3 / Pattern 1 cells.
Recorded audio relies on the instructed unchanged audio settings. These ratios do
not define a gain law, perceived loudness, UI scale or the behavior of every raw code.
The failed alternate-code metadata preparation remains retained separately.

Backup peaks approximately 0.158/0.153 remain suitable at the established level.
The current genuine read-only export is
`experiments/exported-sound3-volume36-001/project.json`. All 31 content hashes and
complete native reconstruction pass; previews retain raw sample codes without
rendering pattern volume.

- [Native checks](../experiments/edited-sound3-volume36-002/hardware-recapture-results-001.json)
- [Ordinary playback measurement](../experiments/edited-sound3-volume36-002/playback-gain-results-001.json)
- [Frozen gain comparison](../experiments/sound3-generated-volume36-gain-results-001.json)
- [Separate hardware observation](../experiments/edited-sound3-volume36-002/hardware-observation-001.json)
- [Lower-interior result](generated-sound3-volume18-results.md)

A [guarded public uniform volume operation](sound3-volume-edits.md) reproduces both
accepted WAVs byte-for-byte. Software reports remain hardware-unverified; new
combinations still need appropriate evidence. The next
[post-playback persistence control](sound3-volume-post-playback-control.md) checks
the current body before any TONE pitch knob action.
