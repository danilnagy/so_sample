# Prior art and related projects

A survey of other work on the PO-33 K.O! backup format and of tools with overlapping
features, made on 2026-11-10 by reading each project's repository or page. Activity and
star counts are as of that date. Corrections are welcome.

## Work on the PO-33 backup format

| Project | Licence, language | What it does | Hardware-verified |
| --- | --- | --- | --- |
| [ericlewis/libpo](https://github.com/ericlewis/libpo) (formerly libpo32) | MIT, C99 | Decodes and encodes PO-33/PO-133 frames (DQPSK modem, whitening, packets); codecs for the settings record (chain, tempo, swing), pattern cells and the effects footer, and sound headers; sample replacement and growth; standalone single-sound transfers; inspection, diff and capture-diagnosis tools; fuzzed parsers. Command line, no GUI or playback model. Extensive format docs (`core/docs/formats/PO33*.md`). PO-33 support merged 2026-11-05. | Yes, for narrow, carefully stated claims (byte-exact sample replacements, resonance endpoints on PO-33 and PO-133, single-sound restores). Leaves key mapping, parameter scales and most effect identities open. |
| [danielpradilla/po-backup-decode](https://github.com/danielpradilla/po-backup-decode) | MIT, Python | Demodulates a backup, checks packet CRCs, exports raw mu-law samples, pattern blobs and BPM. No encoder; note and effect layout unmapped. Published 2026-09-29, the earliest public PO-33 packet decode found. | Transport only. |
| [charlesvestal/po33-backup-re](https://github.com/charlesvestal/po33-backup-re) | MIT, Python | A DQPSK demodulator and documented negative results on the whitening. | No. |
| [potomak/po-33-backup-analysis](https://github.com/potomak/po-33-backup-analysis) | MIT, Python | Notes: about 7.8 kHz DQPSK, repeated backups are bit-identical, the payload is scrambled. | No. |
| [sZXZ/po33-experements](https://github.com/sZXZ/po33-experements) | none stated, Python | Demodulates to bits and re-modulates raw bits; heuristic note export to Strudel and PICO-8. | No. |
| [cspotcode/PO-33-KO-backup-re](https://github.com/cspotcode/PO-33-KO-backup-re) | none stated, TypeScript | The original modem notes (about 7800 Hz, four-phase PSK), recording scripts and a capture corpus (2019 to 2021). | No. |

This project began on 2026-10-11 and was written independently: no upstream code was
copied (see [upstream audit](upstream-audit.md)). libpo's PO-33 work was concurrent and
independent; where the two describe the same fields they agree (for example the settings
record's chain, length, tempo and swing offsets, and resonance at bits 18 to 23).

## What this project adds

- **Every field's musical meaning, measured:** the pitch law and glide, volume table,
  filter bands and resonance levels, the key-to-semitone layout, drum and melodic playback
  rates, and the swing law ([format reference](format-reference.md)).
- **All fifteen punch-in effects, measured** ([FX reference](fx-reference.md)).
- **The four-voice rules:** priority, stealing and release, and the rule that a code 0
  keeps the last locked value.
- **Memory:** the 241-page limit, its failure behaviour, and kits sharing one buffer
  across drum sounds ([kit sharing](kit-sharing-results.md)).
- **Whole projects from a description:** samples, kits, patterns, locks, effects, chain,
  tempo and swing compiled into a restore the device accepts exactly
  ([project build](project-build-results.md)).
- **A browser app** that imports a backup through the audio input, edits it, previews it
  with the device's voice allocation ([web playback](web-playback.md)) and sends it back.
- **Registered hardware experiments:** each claim was predicted before the data was
  taken, and failed predictions are kept ([hardware sessions](hardware-sessions.md)).

## What others do that this project does not

- **Single-sound transfers** (libpo): a restore carrying one sound, leaving the device's
  other sounds in place. Useful for sending one sample without overwriting a project.
- **PO-133 evidence** (libpo): the same frames decode from a PO-133.
- **Tooling:** frame diff and inspection, read-back verification, a capture doctor for bad
  recordings, streaming demodulation and fuzzing (libpo).

## Open question: note length and drum retrigger

The device's own interface sets a melodic note's length (hold a step, turn knob B) and a
drum step's retrigger count (hold a step, press BPM, cycling 1, 2, 3, 4, 6, 8), as
documented in [cubeleco's PO-33 hidden features](https://cubeleco.blogspot.com/2019/05/po-33-ko-hidden-features.html).
libpo's docs associate the auxiliary byte's high nibble with these, units unresolved, and
report drum control bytes 0x19, 0x29, 0x39, 0x49, 0x69 and 0x89, whose high nibbles match
the retrigger cycle.

This project's [stray bits](stray-bits-results.md) test found that the high nibble does
not select a note type and that the app should write F (melodic) and 1 (drum). That test
did not put other nibbles on a drum sound, and its melodic tone may have ended within the
step, so it neither shows nor excludes a length or retrigger meaning. The app therefore
cannot yet write note lengths or retriggers, and its preview ignores them. A registered
experiment (drum steps with nibbles 1 to 8, melodic steps with a long sample and nibbles 1
to F) would settle it.

## Adjacent tools

- **Loading samples by playing audio into the PO-33's own sampler** (no data transfer):
  [rileyjshaw/po-33](https://github.com/rileyjshaw/po-33) (GPL-3.0, browser),
  [POTool](https://github.com/andreaskinga-lgtm/POTool) (desktop, with a lo-fi preview and
  transient slicing), [PocketLab](https://pocket-lab.app/) (web app).
- **PO-33 emulators and helpers:** [jjbenson85/po-33](https://github.com/jjbenson85/po-33),
  [schollz/thirtythree](https://github.com/schollz/thirtythree) (norns),
  [smaudd/PO-33](https://github.com/smaudd/PO-33).
- **PO-32 transfers:** Sonic Charge Microtonic's official PO-32 transfer, whose preview
  also limits itself to four channels; libpo32's open PO-32 modem; and
  [PO-PatchStudio](https://squarewave.studio/po-patchstudio), built on it.
- **EP-133 K.O. II** uses USB SysEx and a different format; see
  [awesome-te](https://github.com/bnjreece/awesome-te) for its tools.
- **Official:** Teenage Engineering publishes [three PO-33 packs](https://teenage.engineering/downloads/po-33)
  as restore audio; there is no official editor.
