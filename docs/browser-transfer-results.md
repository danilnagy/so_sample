# Browser transfer: the web app's Send and Import work on the device

Session 2026-11-11, [registered design](browser-transfer-control.md). Until now the app's
transfer path, a restore played by the browser (Device, Send to PO-33) and a backup
recorded and decoded in the browser (Device, Import from PO-33), had been tested in
software only; the restores accepted by the device came from the Python harness. Here the
bundled project Concrete was sent from the app, read back by the harness, then imported by
the app and exported.

| Prediction | Result |
| --- | --- |
| Send: the backup after the browser's Send equals the compiled target exactly | **held** |
| Import: the app's import of that backup, exported, plays the same as the target (same sound codes and owners, identical patterns, chain, tempo and swing, no more pages) | **held** |

## What happened

- **Send.** Concrete (41 pages, 995 packets, about 50 s) was imported into the app from
  `send-project.sosample.zip` and sent from Device, Send to PO-33, with the computer's
  headphone output into the PO-33's input. The PO-33 accepted it and played Concrete
  afterwards ("yes" to "did PLAY play Concrete?").
- **Read back.** The harness recorded the device's backup through the stereo line input.
  The first recording was 8.2 s long and cut off mid-transfer, and the harness flagged a
  delayed copy of the signal in it (65.6 ms, strength 0.27): the computer's output was
  still connected to the PO-33's input, the feedback the cable swap exists to prevent. The
  second recording, with the cables swapped, decoded at the default threshold and matched
  the target in every packet and the whole body.
- **Import.** The app recorded the device's backup itself (Device, Import from PO-33) and
  created a project, which was exported and saved as `imported.sosample.zip`. Compiled
  again, it gives the same sound codes and owners, identical patterns, chain, tempo and
  swing, and no more pages than the target.

## What this establishes

- The app's Send is a working restore path: a project compiled in the browser and played
  through Web Audio is received by the device exactly, the same result the harness's
  restores have.
- The app's Import is a working backup path: a backup recorded through the browser and
  decoded in the browser comes back as a project equivalent to what the device holds.
- Together with the earlier software round trips, the transfer path a user takes in the
  app is verified end to end on hardware.

## Limits

- One session on one device, with this computer's audio interface and Chrome.
- The send level was not recorded; the instructions and the app's default are 60%. The
  answer to "at what level did the transfer succeed, and how many tries did it take? Did
  the PO-33 ever show ERR?" was recorded as "no", read here as no ERR; the number of tries
  was not noted.
- The import is judged after the app's own export, which fits clip windows to their
  samples as Send does; the browser's decode is not compared packet by packet.
- Other browsers (Safari, Firefox) and other interfaces were not tested. On iPhone and iPad
  the browser's input is mono, so Import cannot work there (the app says so).

- [Registration](../experiments/browser-transfer-registration-001.json)
- [Observation](../experiments/browser-transfer-001/hardware-observation-001.json)
