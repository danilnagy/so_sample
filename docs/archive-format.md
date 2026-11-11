# Project and kit archives

The web app exports a project, or a single drum kit, as a zip whose contents are readable
without the app: one JSON file and the samples as WAV files. The same archive imports
back exactly. The code lives in `web/src/core/archive.ts` (files in memory) and
`web/src/app/archive.ts` (the zip).

## Layout

```
My beat.sosample.zip
  project.json
  samples/
    kick.wav
    pad.wav
```

A kit archive (`<name>.kit.zip`) holds `kit.json` and its `samples/` the same way. A zip
whose contents sit inside one folder, as re-zipping an unpacked export gives, also reads.

## Audio

Each library sample the project references is written once, as a mono 8-bit mu-law WAV
(format tag 7), as imported and before any edits. The bytes are standard G.711, so the
file plays correctly in ordinary tools; the device's own code layout differs from G.711
only in how sign and complement are laid out, and each code maps to exactly one G.711
byte and back, so reimport recovers the codes exactly. WAV headers hold an integer rate, so the header says 23438 Hz; the JSON states the
exact 23437.5 Hz, the code count and a SHA-256 of the codes, and import verifies both.

## project.json

```json
{
  "format": "sosample-project",
  "version": 1,
  "name": "My beat",
  "tempo": 120,
  "swing": 0,
  "chain": [1, 1, 2],
  "sampleRate": 23437.5,
  "samples": [
    {
      "file": "samples/kick.wav",
      "name": "kick",
      "folder": "drums",
      "codes": 48213,
      "sha256": "…",
      "source": { "name": "kick.wav", "rate": 44100 },
      "edits": { "start": 0, "end": 48213, "gainDb": 0, "normalize": true, "fadeIn": 0, "fadeOut": 0, "compressor": null }
    }
  ],
  "sounds": {
    "1": { "sample": "samples/pad.wav", "start": 0, "end": 51200 },
    "9": { "name": "House kit", "keys": { "1": { "sample": "samples/kick.wav", "start": 0, "end": 48213 } } }
  },
  "patterns": [
    {
      "effects": [null, null, 3, null, null, null, null, null, null, null, null, null, null, null, null, null],
      "notes": [
        { "step": 1, "sound": 9, "key": 1 },
        { "step": 5, "sound": 1, "key": 5, "pitch": 15, "volume": 40 }
      ]
    }
  ]
}
```

- Samples are referenced by file path. `edits` appears only when the sample has
  non-destructive edits; `source` records where it came from.
- `sounds` has "1".."8" as clips and "9".."16" as kits, each with an optional `name` and
  its `keys` "1".."16". Windows are in codes of the sample, start inclusive, end exclusive.
  A window reaching past the sample's end is kept as it is, since device backups hold
  such windows and a trim in the sample editor can be undone; the app fits every window
  inside its sample when it plays, compiles or exports the project, and never saves the
  fitted one. A chain holds at most 128 entries, as the device's does.
- `patterns` lists all sixteen. A note's `key` is 1..16, or null for a parameter lock on
  a step without a note. The four parameters are given only when locked (the device's 0
  means "no lock"). `bit5` and `aux` appear only when a device-written pattern carries
  bits the app itself would not write, so every pattern round-trips to its 1032 bytes.
- The preview's mute and solo flags, per sound and per drum key, and the saved kits are
  not part of a project on the device and are not exported.

## kit.json

```json
{
  "format": "sosample-kit",
  "version": 1,
  "name": "House kit",
  "sampleRate": 23437.5,
  "samples": [ … ],
  "keys": { "1": { "sample": "samples/kick.wav", "start": 0, "end": 48213 } }
}
```

## Import

A saved kit exports from its row in the kit editor's Kits menu. A project archive becomes a
new project and opens. A kit archive becomes a saved kit and,
when imported from a sound's kit editor, loads into that sound. A library sample with the
same audio and the same edits is reused rather than duplicated; anything else is added
with its name and folder. Archives with a `version` newer than the app's are refused.
