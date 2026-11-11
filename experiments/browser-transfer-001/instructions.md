# Browser-transfer test, part 1: Send from the app

Do these steps now; the harness records the backup after you press Enter.

1. Start the app from this checkout (`cd web && npm run dev`, then open the address it
   prints in Chrome). The target was compiled by this checkout's code, so use it rather
   than the live site.
2. In the app: Projects, Import project..., choose
   experiments/browser-transfer-001/send-project.sosample.zip. The project "Concrete"
   opens. Do not edit it.
3. Cables: connect the computer's headphone output to the PO-33's input, and unplug the
   PO-33's output from the computer, so the device cannot hear itself.
4. Set the computer's output volume to a fixed, medium level and turn off any sound
   enhancement.
5. On the PO-33, hold write and press sound + record; it waits for the transfer.
6. In the app: Device, Send to PO-33, Play restore, at the default level (60%). It takes
   about 50 s. If the PO-33 shows ERR, try again at another level and note it.
7. When the app says Finished: unplug the computer's output from the PO-33's input, and
   connect the PO-33's output to the computer's stereo line input (the harness's input).

Then press Enter; the harness asks you to start the backup (write + sound + play).
