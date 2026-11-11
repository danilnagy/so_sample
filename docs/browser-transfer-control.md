# Browser-transfer test: the app's Send and Import on the device

Registered 2026-11-11. Every restore so far reached the device from the Python harness. The
web app has its own path: Send plays the restore through the browser (Web Audio), and
Import records a backup through a stereo line input in the browser and decodes it there.
Both are tested in software ([web-app proposal](web-app-proposal.md)); this session runs them
on the PO-33.

## Build

`web/scripts/build-browser-transfer-test.ts` copies the bundled Concrete project archive
(`web/src/presets/concrete.sosample.zip`: 41 pages, a 50 s transfer) into
`experiments/browser-transfer-001/send-project.sosample.zip`, and compiles it exactly as
the app's Send does (`store.buildLabels`: each sample with its edits, windows fitted to their
samples, the empty-device template, kit sharing on) into `packets.json`, and as a restore
into `reference-restore.wav`. That restore is never played; `scripts/prepare_browser_transfer_test.py`
decodes it with the Python decoder into the expected artifact, requires its packets to equal
the compiler's, and registers the predictions. The experiment record names no restore file,
so `po33 hw run` only records and checks the backup.

`web/scripts/check-browser-import.ts` compiles the project the app made from its own
recording, exported as an archive, and compares it with the target. It was checked in
software: a simulated import of the target state, exported as the app exports, passes; the
same export with the tempo changed by one fails on tempo; another project fails on every
sound, pattern and the chain.

## Predictions

Registered in `experiments/browser-transfer-registration-001.json` before the session:

1. **Send.** The backup the device makes after the browser's Send equals the compiled target
   exactly.
2. **Import.** The project the app makes from its own recording of that backup, exported as a
   project archive, compiles to a state that plays the same as the target: every sound the
   same codes from the same owner, every pattern byte for byte, the same chain, tempo and
   swing, and no more pages. (This is the standard the core's import-then-compile tests hold
   device backups to.)

Each is decided independently and kept whether it holds or fails. The level that worked,
retries and any ERR are exploratory, from the session answers.

## Running it

From the repository root on macOS (on Windows use `.\.venv\Scripts\python.exe`). The build
and the registration are done:

```
cd web && npx tsx scripts/build-browser-transfer-test.ts && cd ..
.venv/bin/python -m scripts.prepare_browser_transfer_test
```

**Part 1, Send, with the harness recording the backup.** In one terminal start the app from
this checkout (the target was compiled by this checkout's code, so use it rather than the
live site):

```
cd web && npm run dev
```

In another terminal, start the harness:

```
.venv/bin/python -m po33_re hw run experiments/browser-transfer-001 --no-restore
```

It prints these steps, then waits:

1. In Chrome, at the address `npm run dev` printed: Projects, Import project...,
   choose `experiments/browser-transfer-001/send-project.sosample.zip`. Concrete opens. Do
   not edit it.
2. Cables: the computer's headphone output to the PO-33's input; the PO-33's output
   unplugged from the computer.
3. Output volume fixed and medium, sound enhancements off.
4. On the PO-33: hold write, press sound + record.
5. In the app: Device, Send to PO-33, Play restore (60%). About 50 s. On ERR, try another
   level and note it.
6. When the app says Finished: unplug the computer's output from the PO-33, and connect the
   PO-33's output to the computer's stereo line input.

Press Enter; at the harness's prompt press write + sound + play on the PO-33. The harness
records the backup, checks it against the target on the spot, and asks the questions.

**Part 2, Import in the app.** Cables stay as they are (PO-33 output to the stereo line input).

1. In the app: Device, Import from PO-33. Choose the line input the harness used
   (Check input should report stereo), press Record, then on the PO-33 press write + sound +
   play. The recording stops by itself; the app opens a new project named
   "PO-33 backup <date and time>".
2. Projects, the export icon on that project's row. Save the zip as
   `experiments/browser-transfer-001/imported.sosample.zip`.

**Check and finalize:**

```
.venv/bin/python -m scripts.check_browser_transfer_test
.venv/bin/python -m scripts.finalize_browser_transfer_test
```

The check writes `hardware-recapture-results-001.json` (Send) and
`browser-import-results-001.json` (Import), both whatever the outcome; finalize records the
observation. The results document is written from them after the session.

- [Registration](../experiments/browser-transfer-registration-001.json)
- [Experiment](../experiments/browser-transfer-001/experiment.json)
