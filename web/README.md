# sosample

A browser-only sample, kit and pattern editor for the Teenage Engineering PO-33. Projects
are built in the browser and sent to the device through its line input; backups are read
back through the microphone input. See the [proposal](../docs/web-app-proposal.md).

## Layout

- `src/core/`: framework-free, fully tested. `packets.ts`, `labels.ts` and `state.ts`
  are the backup format (CRC-additive packets, phase labels, canonical device layout);
  `modem/` encodes a restore WAV and decodes a recording; `pattern.ts` and `globals.ts`
  read and write steps, locks, effects, chain, tempo and swing; `mulaw.ts`, `resample.ts`
  and `wav.ts` are the sample pipeline; `project.ts` is the project model with the
  compile (project to device state) and import (device state to project) steps;
  `template.ts` is the empty device state every export starts from.
- `src/core/__fixtures__/`: hardware facts the tests pin to, written by
  `../scripts/export_web_fixtures.py` from verified research sessions. Do not edit by hand.
  `local/` (ignored by git) holds two goldens from the research device's starting state,
  which may include factory audio; their tests skip where they are absent.
- `src/guide/`: the in-app guide, the same app laid out with every view explained.
- `e2e/`: the Playwright browser tests and their screenshot baselines.
- `src/app/`: the React app. `db.ts` (Dexie schema: samples, projects, settings), `store.ts`
  (state and every action, persisted to IndexedDB), `samples.ts` (file import to native
  codes, preview playback), `laws.ts` (display meanings from the measured laws), and
  `device.ts` (send a restore through the audio output, record a backup from the input),
  and `components/` (top bar, pattern bar, FX row, track grid, step inspector, song strip,
  status bar, library, sample editor, clip editor, device dialog). `src/core/edits.ts` holds
  the non-destructive sample modifications.
- `scripts/`: Node scripts, such as the builder of the registered hardware test restore.

## Commands

```
npm install
npm test          # vitest; device-capture tests run when ../experiments holds the recordings
npm run dev
npm run dev:tr    # the same with the TR-sample presets from presets-tr (local only; see ../docs/presets.md)
npm run build     # tsc -b && vite build
npm run lint
npm run test:visual         # Playwright: every modal at phone widths fits the screen and matches its screenshot
npm run test:visual:update  # redo the screenshot baselines after an intended change
npm run presets            # rebuild the bundled kits and projects into src/presets, drums synthesized (see ../docs/presets.md)
npm run presets -- --pack "<TR pack folder>"   # the same from a sample pack, into presets-tr (ignored, local use only)
```

Releasing: `npm run build` writes a static site to `dist/`, presets included; see
[../docs/release.md](../docs/release.md) for hosting requirements and the audit.

The visual tests (`e2e/*.visual.ts`) drive the system Chrome against a dev server they start
themselves, seed a fresh browser profile through the UI (two samples, a melodic sound, a
kit) and, for each modal and popup at 320px and 390px, assert that nothing is wider than
the screen or scrolls sideways, then compare a screenshot with `e2e/__screenshots__`. The
baselines were made on macOS; on another platform regenerate them first and read the diffs.
