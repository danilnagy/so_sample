# Sound 3 live volume changed audibly, with no backup change

The user reported **“done, confirmed that sample is quieter but not silent.”**
No display label, numeric minimum or calibrated gain measurement was supplied.

Both independent captures decode at threshold 0.0063 to 815 checksum-valid packets
ending at byte 156758. Selecting Sound 3 / TONE changes no serialized bytes. Turning
only B fully counterclockwise while stopped and write off also changes no serialized
bytes relative to the fresh selection capture. Both complete bodies exactly equal
the preceding joint 100 BPM / swing 9 project:
`1dab085d95629db191991a089c9e4e67f56fc2a7dd571b1674fa8dbce144e551`.

Every sample code/header, pattern cell, global byte and selector remains exact. The
reported quieter audition after the minimum capture is independent evidence that the
live action had an audible effect. The result supports **no serialized change under
these stopped/write-off conditions**; it does not prove every volume setting is absent
from backups or identify a volume field. The original no-change alternative was
registered before data, and is not treated as a decoding failure.

Channel peaks are approximately 0.160/0.153 with no clipping. The established capture
levels remain suitable. Raw WAVs and decoded artifacts retain hashes in the shared
native report and separate immutable hardware observations. Automated analysis remains
hardware-unverified, and the user result is scoped to quieter rather than silent.

- [Native comparison](../experiments/sound3-tone-volume-probe-results-001.json)
- [Selection hardware observation](../experiments/event-041-a-sound3-tone-selected/hardware-observation-001.json)
- [Minimum hardware observation](../experiments/event-042-b-sound3-tone-volume-minimum/hardware-observation-001.json)
- Current export (`experiments/exported-sound3-live-volume-minimum-001/project.json`, a local research artifact, not in the repository)

The new export verifies all 31 content hashes and reconstructs the unchanged complete
body. Its sample previews use the preserved raw sample codes; they do not reproduce
the quieter live gain, which has no observed representation in these captures.

The next [recorded TONE control](sound3-tone-lock-probe-control.md) uses a fresh plain
playback baseline followed by WRITE-held knob movement. The official guide describes
this as parameter locking for the selected sound. Only B is intentionally moved, but
the TONE pair may snapshot another live setting; volume-specific bitfields remain
unconfirmed. No volume writer is enabled.

All 13 affected observation tests pass. They include genuine no-change capture equality,
strict separation of fresh playback and recorded controls, auxiliary/other-sound/footer
changes and explicit ineffective-lock alternatives. Production writers are unchanged;
the earlier full suite passed 790 tests.
