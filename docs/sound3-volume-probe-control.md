# Sound 3 selection and live TONE volume probe

Start from the accepted **100 BPM / swing 9** state. No restore is needed. Keep
Pattern 1 selected, playback stopped and write off. This probe asks whether a live
sound-volume setting is serialized and where any change appears; no field offset,
display scale, minimum number or target body is assumed.

The [official guide](https://teenage.engineering/guides/po-33/en), section 6, describes
TONE as pitch/volume and FX as the mode selector. Use knob B for TONE volume here.
Leave knob A untouched and do not hold BPM or another button while adjusting B.

1. Select **Sound 3** and **TONE**, without moving either knob or auditioning a note.
   Record a complete backup as
   `experiments/event-041-a-sound3-tone-selected/capture.wav`.
2. Keep Sound 3 / TONE selected and turn **only knob B fully counterclockwise**.
   Note the actual display label and number, if visible. Before playing a note or
   the pattern, record a second complete backup as
   `experiments/event-042-b-sound3-tone-volume-minimum/capture.wav`.
3. After saving the second backup, with write off, tap **keyboard key 1** for Sound 3.
   Report whether it is silent, quieter or unchanged, and any display reading you saw.
   Leave Sound 3 / TONE selected, stopped and write off.

Use the same reduced capture levels and one second trailing silence. Save each file
before the next action. The baseline for the knob change is the fresh selection-only
capture, allowing selection/mode changes to be separated from the volume action.

## Registered alternatives

- Selection may or may not produce a serialized change; compare its complete body
  with the genuine preceding Sound 8 state.
- The live volume action may produce no backup difference. This remains a valid
  outcome; it does not by itself prove that the action worked or that all volume
  settings are excluded. Independent audition/display evidence matters.
- Any changed packet/offset is reported without choosing a convenient candidate
  afterward. Global-only changes, pattern-parameter changes and sample-record changes
  remain explicit alternatives. Tempo 100, swing 9, samples and all patterns have
  separate preservation checks.

No volume writer is enabled. No original volume number or return setting is guessed.
Failed controls and unexpected differences remain in immutable reports.

- [Registration](../experiments/sound3-tone-volume-probe-registration-001.json)
- After decoding both independent captures at threshold 0.0063:
  `python -m scripts.check_sound3_volume_probe --display-text ACTUAL_LABEL --audition-result ACTUAL_RESULT`
- Missing display/audition inputs remain absent rather than being inferred from bytes.

All 27 affected tests pass. They include the accepted joint tempo/swing capture,
explicit unchanged-volume outcomes, fresh selection baselines, raw unexpected changes
and rejection of altered tempo or wrong source identity.

Completed: both captures exactly match the preceding native project, and the user
reports Sound 3 quieter but not silent. No display number was reported. See
[results](sound3-live-volume-results.md). The next probe records TONE parameters in
the pattern through [WRITE-held knob movement](sound3-tone-lock-probe-control.md).
