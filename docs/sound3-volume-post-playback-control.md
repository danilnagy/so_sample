# Post-playback persistence before TONE pitch

The generated 36 backup was recorded before ordinary pattern playback. A new backup
now tests whether that playback leaves the complete body unchanged. The exact-body
prediction is registered before this capture. A mismatch is retained as failed
evidence and examined before any pitch knob action.

Keep both knobs and all audio settings unchanged. Stop playback and ensure write
off. Select Pattern 1 / Sound 3 / TONE without moving either knob, then record a
complete backup as:

`experiments/event-050-a-sound3-volume36-post-playback/capture.wav`

Use the established reduced recording level and one second of trailing silence.
No restore or separate ordinary playback recording is needed. Leave both knobs
untouched afterward. The already recorded ordinary playback supplies the control
action; this capture records its resulting state.

The expected full body is
`c0cc91737d5998aa5d6a214b1eeae0a46213b524d3f5fd307745d1bb780bd39c`, with all 16
Sound 3 / Pattern 1 raw volume values 36, 815 checksum-valid packets and end byte
156758. No TONE pitch field, endpoint code or gain curve is assumed. Recorded
pitch adjustment is a later control after this persistence result.

- [Preregistration](../experiments/sound3-volume36-post-playback-registration-001.json)
- [Accepted source observation](../experiments/edited-sound3-volume36-002/hardware-observation-001.json)
- [Upper-interior results](generated-sound3-volume36-results.md)

Completed: the entire body and all packets remain unchanged, including all 16 volume
values. See [results](sound3-volume-post-playback-results.md) and the next
[recorded TONE pitch probe](sound3-tone-pitch-probe-control.md).
