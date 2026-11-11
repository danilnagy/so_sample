# PO-33 backup format reference

Everything an editor needs, as verified on the device. Each line links to the result that
established it.

## Transport and framing
- Staggered-quadrature phase modem; the frame starts at wire byte 4095; CRC-additive
  whitened packets ([modem and packet docs](field-map.md)).
- Packet tags: 0x68B5 sound selector, 0xEF78 sound data, 0xA041 pattern selector, 0xC498
  pattern data, 0x7D5C global record.
- Restore and backup each take about 0.27 s per 1000 sample codes; keep unused sounds
  small ([hardware sessions](hardware-sessions.md)).

## Samples
- Signed mu-law codes at 23437.5 Hz. A sound record is a 9-byte header (start u32, end
  u32, owner byte) followed, for an owner, by its buffer in 4096-code pages
  ([drum recording](drum11-record-observation-results.md)).
- Melodic slot s owns sound id s-1 ([all melodic slots](all-melodic-slots-results.md)).
  Drum slot N owns ids 8+16(N-9) to +15, one per key; the kit is one buffer under the
  first id with 15 references, contiguous windows in key order; key k plays window k at the
  stored rate ([drum notes](drum-notes-writer-results.md), [kit import](drum-kit-import-results.md)).
- A record plays from its start code to its end code, so samples are trimmed by the header
  ([sample window](sample-window-results.md)). Any whole number of pages is a valid
  capacity ([pages](drum-kit-pages-results.md)); a 4 s melodic sample works
  ([long melodic](long-melodic-results.md)).
- Total sample memory is 241 pages, 987136 codes, 42.1 s; a larger restore ends in ERR
  and keeps a 241-page prefix ([limit](sample-memory-limit-results.md)).
- Melodic playback frequency = stored x 2^((7 + key offset + pitch - 13)/12)
  ([Sound7 import](sound7-import-results.md)); drums play at the stored rate x
  2^((pitch - 13)/12) ([drum pitch](drum-pitch-results.md)).

## Patterns
- 1032 bytes: 16 steps x 16 sounds x 3 primary bytes, then 256 auxiliary bytes, then an
  8-byte effects footer.
- Auxiliary byte: 0xF0 | (key-1) for a melodic note, 0x10 | (key-1) for a drum note, 0 for
  no note. The high nibble is a drum note's retrigger count and a melodic note's length
  ([aux nibble](aux-nibble-results.md), [2](aux-nibble-2-results.md), [3](aux-nibble-3-results.md)):
  - Drum: 1, 2, 3, 4, 6 or 8 hits, one every step/n (5 and 7 play as 6 and 8). The
    repeats re-strike the note's one voice, each restarting the sample, and never cut
    other sounds.
  - Melodic: n steps for 1 to E; F plays the sample to its end (the default).
  - Under swing (exploratory, one session): a delayed step's note still ends on the
    unswung grid, so it loses the delay; a delayed drum step plays only the repeats
    that fall before the next step's grid line.
  F and 1, a full-length note and a single hit, are the defaults ([stray bits](stray-bits-results.md)).
- Primary bytes, 24 bits little-endian: pitch bits 0-4, bit 5 inert, volume 6-11, filter
  12-17, resonance 18-23 ([note bits](note-bits-results.md), [bit 5](bit5-glide-results.md)).
- Code 0 in any parameter means no lock: the step keeps the last locked value; a cell with
  primary bytes but a zero auxiliary byte is a lock without a note and counts
  ([no lock](no-lock-results.md), [parameter-only](param-only-results.md)). The value before
  any lock is live device state that a backup cannot set ([knobs](sound-knobs-results.md));
  a restore leaves it inaudible for auditions by hand, playing a pattern does not change
  it, and the knobs set it ([auditions](audition-lock-results.md)).
- Pitch 1..25: one semitone per code around 13, with a 25 to 35 ms glide into each note
  ([pitch law](pitch-law-results.md)). Volume: measured gain table, about 0.4 dB per code
  mid-range ([volume law](volume-law-results.md)). Filter: 0 and 63 off, 1-26 low-pass with
  the edge from 400 Hz to 7 kHz, 27-31 low-pass above 10 kHz, 32-43 flat, 44-62 high-pass
  from 400 Hz to 9 kHz ([filter law](filter-law-results.md)). Resonance: eight levels of
  eight codes, peak rising about 20 dB ([resonance law](resonance-law-results.md)).
- Key layout, semitones from key 1: 0,+1,+3,+4 / -7,-5,-4,-2 / -12,-11,-9,-8 / -19,-17,-16,-14
  ([key scale](pattern1-key-scale-map-results.md)).
- Effects footer: see the [FX reference](fx-reference.md).

## Voices
- Four voices. On a shared step the lowest sound numbers win, except Sound 11 ranks right
  after Sound 3 ([polyphony](polyphony-results.md), [priority](priority-map-results.md)).
- A sounding note is never cut to make room; a new note plays only if a voice is free or
  within about 100 ms of its end ([stealing](voice-steal-results.md),
  [release](voice-release-results.md)).

## Globals (second 0x7D5C record)
- Bytes 0-127: the pattern chain, entries counted from zero; byte 128: chain length. The
  selected pattern is a chain of one ([chain](pattern-chain-results.md),
  [selected](selected-pattern-results.md)).
- Byte 129: tempo in BPM, 60-240. Byte 130: swing 0-18; even steps are delayed by
  swing/24 of a step ([swing law](swing-law-results.md)).
- Bytes 131-146: one per pattern, stored as written, no audible effect; leave alone
  ([stray bits](stray-bits-results.md)). Bytes from 147, and the whole first record, are
  unwritten filler.

- Sharing: a sample stored once under one sound can be referenced by other melodic sounds
  and drum slices, each with its own window; a drum key with no record is silent; a kit may
  mix its own buffer with references ([web template](web-template-results.md)), including
  references into another drum sound's kit buffer, so a kit loaded on several drum sounds
  is stored once ([kit sharing](kit-sharing-results.md)).

## Building a project
`po33_re.project_build` turns a spec of samples, patterns, chain, tempo and swing into a
restore that the device accepts exactly ([project build](project-build-results.md)). The
plan operations it uses are listed in [edit plans](edit-plans.md).
