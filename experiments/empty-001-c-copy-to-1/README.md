# Copy the existing sound into Sound1

The current two Sound8-only backups match exactly. This control copies that stored
sound into the empty melodic slot1, retaining Sound8, without another analogue recording.
It tests slot placement and whether copied sound content is reusable in the transport.
Transfer size and sample allocation sharing are observations, not assumed results.

1. Keep the sequencer stopped and write mode off. Select **Sound8** with **sound + 8**.
2. Hold **write + sound**, press **1**, then release the buttons. This copies the selected
   sound to slot1 according to the [official guide](https://teenage.engineering/guides/po-33/en).
3. Reselect **Sound8** with **sound + 8**. Keep **Pattern1** selected, write mode off and
   playback stopped. Keep patterns empty and other controls/settings unchanged.
4. Record one full stereo backup as **capture.wav in this folder**, using the current
   recording settings. Leave Sound1 and Sound8 populated afterward.

No new line-input recording, fresh before-state or return capture is needed for this
first copy control. The existing Sound8-only pair is explicitly reused. Exact button
actions and any unexpected display/memory behavior should be reported with the upload.
Copying is performed by the user on the device; no tool has modified hardware state.
