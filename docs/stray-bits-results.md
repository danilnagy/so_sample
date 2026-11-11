# Stray bits: the device stores anything; only F and 1 matter

The [stray bits observation](stray-bits-control.md) gave the device auxiliary high
nibbles it never writes, and set global bytes 131 to 146 to 1 through 16. The backup
equals the target exactly: every raw cell and every global byte came back as written. Both
registered hypotheses hold; the odd steps played normally.

What the even steps played, read exploratively:

| Step | Cell | Played |
| --- | --- | --- |
| 2 | Sound 8, nibble 2, key 1 | a normal key-1 note at 784 Hz |
| 4 | Sound 8, nibble 1 (the drum nibble), key 1 | a normal key-1 note at 784 Hz |
| 6 | Sound 13, nibble F (the melodic nibble), key 1 | the drum's 300 Hz tone at full length, but entering from about 163 Hz and rising to 300 Hz over 120 ms |
| 8 | Sound 8, nibble E, key 1 | a normal key-1 note at 784 Hz |
| 10 | Sound 8, parameter-only cell | silence |
| 12 | Sound 8, key 6 with the pitch field 0 | key 6 at the held pitch: 587 Hz |

So the high nibble does not select a note type. On a melodic sound any nonzero nibble
plays the key in the low nibble; on a drum sound the melodic nibble plays the slice at the
stored rate with a glide in, which may be the melodic glide applied to a drum. Global
bytes 131 to 146 are stored and had no audible effect on a single-pattern chain; the
earlier reading of them as per-pattern stop steps stands as a hypothesis. An editor should
write only F for melodic notes and 1 for drum notes, and leave bytes 131 to 146 alone.

With this, every field of a backup has a known role, a measured non-effect, or, for bytes
131 to 146, a harmless uncertainty.

Later note (2026-11-10): no drum step here carried a nibble other than 1, and the melodic
tone may have ended within its step, so this test neither shows nor excludes the nibble
holding a note length or retrigger count, as the device's interface and other work suggest
([prior art](prior-art.md#open-question-note-length-and-drum-retrigger)).

- [Registration](../experiments/stray-bits-registration-001.json)
- [Decision](../experiments/stray-bits-decision-001.json)
- [Observation](../experiments/compiled-stray-bits-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-stray-bits-001/project.json`
