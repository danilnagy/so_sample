# Volume 36 persists after ordinary playback

The fresh full backup after the recorded ordinary playback matches the accepted
uniform 36 body and all packets exactly:
`c0cc91737d5998aa5d6a214b1eeae0a46213b524d3f5fd307745d1bb780bd39c`.
All 815 checksums and end byte 156758 are valid. The complete-body persistence
prediction passes; all 16 raw volume values remain 36. Samples, notes, globals
and every other byte are unchanged. No new audible or numeric UI claim is inferred
from the user's "done".

Backup peaks approximately 0.156/0.150 remain suitable at the established level.
All 31 content hashes and complete native reconstruction pass for the current
genuine read-only export:
`experiments/exported-sound3-volume36-post-playback-001/project.json`.

- [Immutable persistence checks](../experiments/event-050-a-sound3-volume36-post-playback/persistence-results-001.json)
- [Separate hardware observation](../experiments/event-050-a-sound3-volume36-post-playback/hardware-observation-001.json)
- [Original preregistration](../experiments/sound3-volume36-post-playback-registration-001.json)

This rules out a stored change from the ordinary playback in this control. It does
not identify TONE pitch or imply that writing while moving a knob preserves volume.
The next [recorded TONE A control](sound3-tone-pitch-probe-control.md) compares with
this actual post-playback baseline. Production volume-edit guards remain unchanged.
