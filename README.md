# SoSample: the PO-33 K.O! backup format, decoded

[![Netlify Status](https://api.netlify.com/api/v1/badges/127e3ad5-ade1-4d9f-9103-4d29c1033b31/deploy-status)](https://app.netlify.com/projects/sosample/deploys)

**Try it: [sosample.com](https://sosample.com).** Source: [github.com/danilnagy/so_sample](https://github.com/danilnagy/so_sample).

The Teenage Engineering PO-33 K.O! has no USB data port. Its whole state (samples, kits,
patterns, parameter locks, effects, song chain, tempo and swing) travels as a stereo
audio signal through the 3.5 mm jack: the device plays a *backup* and listens for a
*restore*. This project decodes that signal and the state it carries, documents every
field, and writes restores the device accepts byte for byte.

It has three parts:

- **A format reference** backed by registered hardware experiments
  ([format reference](docs/format-reference.md), [FX reference](docs/fx-reference.md)).
- **SoSample, a browser app** (`web/`) that builds samples, kits, patterns and songs,
  previews them with the device's four-voice behaviour, imports a backup through the
  computer's audio input and sends a restore back. It runs entirely in the browser; nothing
  is uploaded.
- **A Python research toolkit** (`src/po33_re/`) that decoded the format: modem, packets,
  field readers and writers, and the harness that runs a hardware session.

SoSample is an independent project, not affiliated with or endorsed by Teenage
Engineering. PO-33 and K.O! are their trademarks.

## Status

The format is decoded for an editor's purposes: samples and memory, kits and slices,
pattern notes and keys, pitch, volume, filter and resonance locks, all fifteen effects,
the chain, tempo and swing. Every claim was predicted before the data was taken and
checked on a PO-33: a restore is sent, a fresh backup is read back and compared byte for
byte, and where it matters the playback is recorded and measured. Whole projects built
from a description are accepted exactly ([project build](docs/project-build-results.md)).

The web app is complete for a first, local-only release: projects, kits and a sample
library in the browser's storage, ten bundled projects and seven drum kits, undo, a
phone layout, an in-app guide (the **?** button), and offline use after the first visit.

The app's own Send and Import are verified on the device: a project sent from the browser
is received exactly, and the browser's import of the device's backup is equivalent
([browser transfer](docs/browser-transfer-results.md)). The latest format finding: a step's
auxiliary nibble holds a drum's retrigger count and a melodic note's length in steps
([aux nibble](docs/aux-nibble-results.md), [2](docs/aux-nibble-2-results.md),
[3](docs/aux-nibble-3-results.md)); the app writes and previews both. Remaining open
questions are listed where they apply.

## Quick start: the web app

Node 22 or later.

```sh
cd web
npm install
npm run dev          # http://localhost:5173
```

To send a project, connect the computer's headphone output to the PO-33's line input,
put the device in restore mode (hold **write**, press **sound** + **record**), and use
Device, Send to PO-33. To import, connect the PO-33's output to a **stereo** line input
(a built-in microphone is mono and cannot carry a backup), hold **write** and press
**sound** + **play**, and use Device, Import from PO-33. The guide explains every view.

| Command (in `web/`) | Does |
| --- | --- |
| `npm test` | Unit tests (Vitest): format core, compiler, store |
| `npm run test:visual` | Browser tests (Playwright, system Chrome) at phone widths, with screenshot baselines |
| `npm run lint` | oxlint |
| `npm run build` | Static site in `web/dist/`; see [release](docs/release.md) |
| `npm run presets` | Rebuild the bundled kits and projects; see [presets](docs/presets.md) |

## Quick start: the Python toolkit

Python 3.12.

```sh
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev,hardware]"
.venv/bin/python -m pytest
.venv/bin/ruff check src tests
.venv/bin/python -m po33_re --help
```

On Windows the same steps are `py -3.12 -m venv .venv` and `.\.venv\Scripts\python.exe`;
the research docs were written on Windows and show that form throughout.

Many tests replay the research recordings, which are not in the repository (about 12 GB
of device audio). Without them those tests skip, and the rest run: 537 pass in a fresh
clone.

## Working with the device

```sh
.venv/bin/python -m po33_re hw devices
.venv/bin/python -m po33_re hw config --input <n> --output <n>
.venv/bin/python -m po33_re hw run experiments/<folder>
```

`hw run` plays a prepared restore, prompts for the cable swap (the PO-33 must never hear
its own output), records the backup, checks it against the target and records the
playback. Each experiment has a `scripts/prepare_*`, `check_*` and `finalize_*` script;
predictions are registered before the session and failed ones are kept. See
[hardware sessions](docs/hardware-sessions.md).

## Documentation

**The format**
- [Format reference](docs/format-reference.md): every verified fact, each linked to the
  experiment that established it.
- [FX reference](docs/fx-reference.md): the measured behaviour of each effect.
- [Kit sharing](docs/kit-sharing-results.md): drum sounds playing from another kit's buffer.
- [Packet decoding](docs/packet-decoding.md), [transport](docs/transport.md): the modem
  and packet layers.

**The web app**
- [Proposal](docs/web-app-proposal.md): the design and its phases.
- [Archive format](docs/archive-format.md): the project and kit files it exports.
- [Web playback](docs/web-playback.md): what the preview reproduces and approximates.
- [Presets](docs/presets.md): the bundled kits and projects and how they are built.
- [Sound synthesis](docs/sound-synthesis.md): how every bundled sound is synthesized, as a
  reference for reuse.
- [Release](docs/release.md): building, hosting and the release audit.

**The research**
- [Hardware sessions](docs/hardware-sessions.md) and [edit plans](docs/edit-plans.md).
- [Status log](docs/status-log.md): the chronological record.
- [Prior art](docs/prior-art.md): related projects and how this one compares.
- [Follow-ups](docs/follow-ups.md): open questions and ideas for later.
- [DEVELOPMENT.md](DEVELOPMENT.md): the original implementation brief (historical).

In the research docs, "the user" is the person operating the device during a session.
`CLAUDE.md` holds the working conventions for the AI assistant used during development.

## Repository layout

| Path | Holds |
| --- | --- |
| `web/` | The browser app. `src/core/` is the framework-free format code (modem, packets, patterns, project compiler), `src/app/` the React app, `src/guide/` the in-app guide, `scripts/` the preset and test-restore builders, `e2e/` the browser tests. |
| `src/po33_re/` | The Python reference implementation and hardware harness (`python -m po33_re`). |
| `scripts/` | One prepare, check and finalize script per hardware experiment, and analysis tools. |
| `tests/` | The Python tests. |
| `experiments/` | Every experiment's registration, results and observations as JSON. Audio captures and derived files are not published; results pin them by hash. |
| `docs/` | References, and the control and results document of each experiment. |

## Samples and licensing

The code and documentation are released under the [MIT licence](LICENSE).

The bundled drum kits are synthesized by `web/scripts/drum-synth.ts`
([sound synthesis](docs/sound-synthesis.md)): they mirror the
layout and character of seven TR-series machines without using any recorded audio, and
the chords, basses and leads come from the generators in `web/scripts/`. All of it is
covered by the same licence. Kits built from third-party sample packs can be made for
local use (`npm run presets -- --pack <folder>`, see [presets](docs/presets.md)); that
output is ignored by git.

Recordings of the research device are not published, since its starting state may have
held factory sample content. Two golden test fixtures derived from it are likewise kept
local; their tests skip without them.

## Credits

The PO-33 modem was first explored in public by
[cspotcode/PO-33-KO-backup-re](https://github.com/cspotcode/PO-33-KO-backup-re), and
the PO-32's transfer, a close relative, by Sonic Charge's Microtonic and
[libpo32](https://github.com/ericlewis/libpo32), whose whitening scheme this project
verified for the PO-33. [ericlewis/libpo](https://github.com/ericlewis/libpo) and
[danielpradilla/po-backup-decode](https://github.com/danielpradilla/po-backup-decode)
decoded the PO-33 format independently. [cubeleco's notes](https://cubeleco.blogspot.com/2019/05/po-33-ko-hidden-features.html)
document the device's hidden controls. See [prior art](docs/prior-art.md) for the full
survey. No upstream code was copied ([upstream audit](docs/upstream-audit.md)).
