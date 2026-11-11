# Proposal: sosample, a PO-33 sample, kit and pattern editor in the browser

Name: **sosample**, at sosample.com.

Current status (2026-11-10): all phases through 5 are built, including the device-faithful
preview ([web playback](web-playback.md)), ten bundled projects and seven synthesized kits
([presets](presets.md)), undo, a phone layout and an in-app guide. The app is released as a
local-only static site ([release](release.md)) and the repository as open source under the
MIT licence. The history below is kept as written.

Status: decisions confirmed 2026-10-11. Phase 1 core written the same day (`web/src/core`,
34 tests): the TypeScript encoder reproduces the accepted restore WAVs byte for byte, the
decoder recovers the device recordings, and the compile step's first restore was accepted by
the device exactly ([results](web-template-results.md)). Phase 2 (app shell) written the same day: projects and samples in IndexedDB, track grid, step inspector, FX row, song strip, status bar, library modal with import, themes, restore WAV download. Phases 3 and 4 written 2026-11-06:
sample editor and clip windows; send and record in the browser (Web Audio, AudioWorklet tap, no input
processing), import from a recording file; software round trip tested, device run pending.

Decisions taken:

- One project is one PO-33 state. Users keep and edit several projects locally. A project
  holds up to 8 melodic and 8 drum tracks, or none. The samples library is shared and any
  track may reference any sample.
- Loading a sample into a track is refused when the project would exceed the device's
  241 pages of sample memory.
- Drum tracks are filled with one sample per slice, each with its own window. No
  auto-slicing, and no spreading one sample over the sixteen keys.
- Imported samples become new library entries; no content matching.
- Browser permission prompts for line-in are acceptable. No verification backup after
  export for now.
- Additional hardware tests are fine when the app needs them (template state, memory
  sharing).
- Sequencer preview is a follow-up.
- React with TypeScript. Compression as threshold, ratio and makeup gain, plus normalize
  and fades; stereo files are mixed to mono on import. Desktop first, all major browsers.
- Private repository for now; license later.
- Git: Claude provides commands, the user runs them (see CLAUDE.md).
- Browser-only, confirmed again on 2026-10-11 after weighing a server-side codec on
  Netlify Functions: payload sizes (up to 46 MB per transfer), the free tier's cost and the
  intent to open-source the project decided it. Encoding and decoding run in the browser and
  work offline; no backend.

## 1. What the device format allows the app to do

The reverse-engineering work is complete enough to drive an editor
([format reference](format-reference.md), [FX reference](fx-reference.md)). The facts that
shape the app:

- A PO-33 backup is one file holding 16 sounds, 16 patterns, a pattern chain, tempo and
  swing. Restore and backup are all-or-nothing: the app always sends a complete state.
- Sounds 1 to 8 are melodic (one sample each, 16 keys on a fixed scale). Sounds 9 to 16
  are drum kits (16 slices, one per key, stored as 16 windows into one buffer).
- Sample memory is 241 pages of 4096 mu-law codes at 23437.5 Hz, about 42 s in total,
  allocated in whole pages per sound. Transfer time is about 0.27 s per 1000 codes each
  way, so a full device takes about 4.5 minutes per direction.
- A step holds, per sound, one note (key 1 to 16) and four parameters: pitch, volume,
  filter and resonance. Code 0 means "no lock, keep the last value"; a lock can sit on a
  step with no note. A sound has no stored base settings: the knob positions are live
  device state, so the only way to set a sound's filter is a lock.
- Each step of a pattern has one optional effect, 1 to 15, applied to the whole mix.
- Four voices; on a shared step the lowest sound numbers win, with Sound 11 ranking just
  after Sound 3; a sounding note is never cut to make room.
- The chain holds up to 128 entries; tempo is 60 to 240; swing 0 to 18 delays even steps
  by swing/24 of a step.

## 2. Clarifying questions (answered where marked)

1. **Project model.** Is one app project exactly one device state, or are kits and
   pattern sets reusable pieces assembled into a project at export time? The former is
   simpler and matches the device; the latter matches "compose kits and pattern sets".
2. **Multiple projects.** Should users keep several projects locally and switch between
   them, or is there one working project plus the library?
3. **Drum tracks.** Answered: a drum track is 16 slices, each assigned its own sample and
   window. An equal "Slice ×16" spread of one sample was built and later removed.
4. **Import.** Answered: imported samples become new library entries and an imported state
   becomes a new project.
   The remaining questions below were all answered on 2026-10-11; see the decisions above.
5. **Audio I/O.** The browser can play the restore through the default output and record
   line-in through the microphone permission. Is a browser permission prompt acceptable,
   and should the app offer an optional verification backup after each export, as the
   research harness does?
6. **In-app playback.** Is a sequencer preview needed in the first version, or only sample
   auditioning? A faithful preview means reproducing pitch, filter, resonance, four voices
   and the effects; an approximate one is a large but well-specified piece of work.
7. **Framework.** React with TypeScript is my recommendation, for the audio and
   worker ecosystem; Vue is equally viable. Which do you prefer?
8. **Sample editing.** Compression: a simple threshold, ratio and makeup gain? Also
   normalize and fade in/out? Where does mono mixdown of stereo files happen?
9. **Browsers and devices.** Desktop first? Chrome, Edge, Firefox and Safari all do
   Web Audio, but Safari's recording path needs care.
10. **Open source and licensing.** Will the repository be public, and under which license?
    Answered 2026-11-10: public, MIT.
11. **Research data.** The 12 GB of captures stays out of git by the current ignore rules.
    Should it be archived separately? Answered: the captures stay private and are not
    published; results pin them by hash.

## 3. Recommended UI

### Track rows

A track header, then 16 step cells. Header contents:

- Type badge: melodic or drum.
- Sample: the sample name, which opens the library. For a drum track, a 4x4 slice grid
  showing which keys have a sample; clicking a slice opens the library for that key.
- Mute and solo, app-only.
- A memory readout: pages this track will use on the device.

There are no device-level sound options to show, because the device stores none.

### Step cells

- A note shows its key number. A lock without a note shows as a hollow cell with a small
  mark. Empty is blank.
- Selecting a cell shows a step inspector to the right of the grid with: key (1 to 16,
  with the melodic note name or slice number), and the four parameters, each with an
  explicit "no lock" state and a value. Filter shows its meaning: off, low-pass with
  cutoff in Hz, high-pass with cutoff in Hz. Resonance shows its level 1 to 8. Pitch shows
  semitones. Volume shows dB from the measured table.
- Shift-click or drag to set the same key on several steps; typing a number sets the key.

### Pattern row and effects

- Sixteen pattern buttons above the first track, the selected one filled. Buttons with
  content get a dot. Copy and clear patterns from a small menu.
- Below the pattern buttons, an FX row of 16 cells, one per step, showing the effect
  number for the current pattern. Hovering shows the measured description.

### Song (chain)

A horizontal strip of chips under the pattern row, each chip a pattern number. Click a
pattern button with shift held to append it; drag chips to reorder; a chip's close mark
removes it; a counter shows the length out of 128. The first chip is what the device
plays after a restore. A plain strip is enough; a grid would misrepresent a chain, which
has no fixed width.

### Status bar

Tempo, swing, memory used out of 241 pages, voices in use on the selected step out of
four, and a modified indicator for samples.

### Style

Single background, single foreground, one-pixel borders, one radius, system or chosen
light or dark theme through CSS variables. No color beyond the two tones, with a filled
cell meaning "on".

## 4. Sample library and editor

A modal over the track view.

- Folders as a left column; samples as a list with name, length, memory pages and a
  modified mark. Upload WAV (drag and drop or picker), download WAV, rename, move,
  delete.
- Editor: waveform with start and end handles, gain, a simple compressor, and a preview
  button. Edits are stored as a modification record next to the original and applied on
  export. "Resample" bakes them into a new WAV, replacing or copying.
- Device readiness panel: the sample's length at 23437.5 Hz, its page count, and a
  warning when it would exceed the melodic length verified so far or the device total.

Samples imported from the device keep their window as a modification, so a trimmed
sample imports as the original buffer plus a crop.

## 5. Architecture

- **Framework.** React 19, TypeScript, Vite. State in a small store. IndexedDB through
  Dexie for samples (as blobs), projects and modifications. A repository interface wraps
  storage so a cloud adapter can be added for the premium tier without touching the UI.
- **Workers.** Encoding, decoding, resampling and sample analysis run in Web Workers.
  Recording runs in an AudioWorklet.
- **Core library** (`web/src/core`, framework-free, fully unit-tested):
  - format: packets, CRC, whitening, sound records, pattern cells, globals;
  - modem: encoder to PCM and decoder from PCM, ported from the Python;
  - project model and the compile step from model to device state;
  - sample pipeline: decode WAV, mono mixdown, resample to 23437.5 Hz, mu-law, apply
    modifications;
  - memory budget and voice checks.
- **Deployment.** The web app lives in `web/` with its own package.json; Netlify builds
  from that base directory to a static site at sosample.com. No backend.

## 6. Translation and decoding work still needed

The decoding is done; the remaining work is translating it and closing a few engineering
gaps.

1. **Port the modem and format code to TypeScript.** The Python encoder and decoder are
   the reference. Golden tests: every verified restore WAV in the research set must be
   reproduced byte for byte by the TypeScript encoder from its symbol artifact, and every
   verified capture must decode to the same bytes. The harness lessons carry over: 20 ms
   onset skip, realignment of a slipped leading label, padding before and after the
   restore, constant playback level.
2. **Template state.** The app starts every export from the empty device backup
   (experiments/empty-001-a, `web/src/core/template.ts`) and writes only the fields it
   understands, leaving the filler and bytes 131 to 146 as the device left them. Verified:
   a project built on it restored exactly ([results](web-template-results.md)), which also
   covered the sharing layouts of item 4 and an empty drum key stored as an absent record.
3. **Import model.** Readers exist for everything in a backup. The app needs one function
   that turns a decoded backup into the project model, including factory references into
   another sound's buffer, which become a sample plus a window.
4. **Memory sharing.** Confirmed as a requirement: when two tracks use the same library
   sample with the same modifications, the sample is uploaded once and the second sound
   references the first sound's buffer. The device format supports this, the factory
   content uses it, and a generated melodic reference restored exactly in the earlier
   research ([Sound 6 to 7 copy](sound6-to7-generated-copy-results.md)). The existing
   writer only covers that one slot pair, so the compile step needs a general reference
   writer, and two hardware sessions should verify it before release: a melodic sample
   shared between two melodic tracks with different windows, and a sample shared between a
   melodic track and a drum slice, as the factory content does between Sounds 1 and 9.
   Samples whose modifications differ are separate uploads, since the window is the only
   per-reference difference the format allows.
5. **Longer melodic samples.** Verified to 4 s. Anything up to the memory limit is very
   likely fine, but a 20 s single sample has not been restored. One session if wanted.
6. **Preview engine (optional).** All the laws are measured. A preview that applies the key
   and pitch laws, the glide, the volume table, the filter and resonance curves, four-voice
   allocation and the effects catalogue is a self-contained module; the research data gives
   it tests.

## 7. Finalizing the research work for a first commit

The repository has no commits yet. Before the web app starts:

1. **README.** It is now a 2766-line status log. Replace it with a short overview linking to
   the format reference, FX reference, hardware sessions guide and edit plans, and move the
   chronological entries to `docs/status-log.md`.
2. **Experiments.** The ignore rules already exclude WAV, npz, derived and attempt folders,
   so git keeps about 4900 small JSON registrations, results and observations and none of
   the 12 GB of audio. Archive the audio separately once, since the results JSON pins it by
   hash.
3. **Housekeeping.** Remove stray pytest cache folders, confirm the lock file, add a
   license, run lint and the 1505 tests, and tag the commit as the research baseline.
4. **Layout.** Keep the Python toolkit at the root as the reference implementation and
   research harness. Add `web/` beside it. The Python stays the source of test fixtures for
   the TypeScript port.

## 8. Phases and rough size

| Phase | Content | Size |
| --- | --- | --- |
| 0 | First commit as above | small |
| 1 | TypeScript core: format, modem, model, compile, golden tests against Python | done, hardware verified 2026-10-11 |
| 2 | App shell, storage, track grid, patterns, FX row, song strip, themes | done |
| 3 | Sample library and editor, modifications, resample | written 2026-11-06 |
| 4 | Export with guided protocol and optional verify; import with recording and decode | done; verified on the device 2026-11-11 ([browser transfer](browser-transfer-results.md)) |
| 5 | Preview engine | done ([web playback](web-playback.md)) |
| 6 | Accounts and cloud backup | later |

Phase 1 and 2 can proceed in parallel. The first usable milestone is the end of phase 4:
build a project in the browser, send it to the device, read one back.
