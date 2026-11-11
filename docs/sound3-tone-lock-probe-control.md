# Plain playback and recorded Sound 3 TONE probe

The live stopped-mode volume action made Sound 3 quieter without changing the complete
backup. The next probe asks whether a **recorded TONE adjustment** changes pattern
data. No restore is needed. Keep Pattern 1 / Sound 3 / TONE, tempo 100 and swing 9,
with knob A untouched throughout.

The [official guide](https://teenage.engineering/guides/po-33/en), section 6, specifies
holding WRITE and turning knobs while playing to lock TONE or FILTER parameters for
the selected sound. This experiment intentionally moves only B.

1. With write off and both knobs untouched, play Pattern 1 for approximately
   **3 seconds**, then stop. Save a complete backup as
   `experiments/event-043-a-sound3-plain-playback/capture.wav`.
2. Start Pattern 1 again. **Hold WRITE** and slowly turn **only B clockwise to its
   maximum over about 5 seconds**. Continue holding WRITE for **3 more seconds**
   with both knobs stationary. Do not press keyboard keys or hold BPM/FX.
3. Release WRITE, stop playback, and ensure the write indicator is off. Save a complete
   backup as `experiments/event-044-b-sound3-tone-volume-lock-up/capture.wav`.
4. Report whether Sound 3 became louder during the adjustment and any display label
   or number you saw. Leave Pattern 1 / Sound 3 / TONE, stopped and write off.

Use the same reduced capture levels and one second trailing silence. Save A before
starting the recorded pass. No separate ordinary playback recording is required yet.

## Registered predictions and limits

Plain playback A is predicted to preserve the complete known body, but that prediction
is independently checked. The earlier minimum capture was saved before audition;
fresh A controls for that audition and plain playback without writing. Lock B must
be compared with **actual A**, even if A differs from the earlier project.

The location alternatives are changes confined to Pattern 1's Sound 3 primary cells,
changes including those cells' auxiliary values, or no serialized change. Every
3-byte primary tuple remains opaque. Existing keys and event flags are not decoded
after a TONE pass, and changed cells at previously empty steps remain visible without
being labeled newly triggered notes. Other sounds, the pattern footer, other 15 patterns,
samples, global settings and packet geometry have separate preservation checks.

The five-second ramp and stationary hold **do not predict an identical maximum value
at every step**. No maximum display number, target body or volume-specific bitfield is
guessed. Only B is intentionally moved, but recording the TONE pair may snapshot another
live parameter. A broader change is retained as an outcome, not silently interpreted
as volume. No volume or pitch-field writer is enabled.

- [Registration](../experiments/sound3-tone-lock-probe-registration-001.json)
- After independent decoding at threshold 0.0063:
  `python -m scripts.check_sound3_tone_lock_probe --display-text ACTUAL_LABEL --audition-result ACTUAL_RESULT`
- Missing display and audition inputs stay absent; field values are never inferred
  from the user's lack of a number.

All 13 affected tests pass, including actual live-volume no-change evidence and
rejection of hidden auxiliary, other-sound, footer or baseline differences.

Completed: plain playback preserves the body, while the recorded pass changes 32
primary bytes in all 16 Sound 3 cells only; the user hears louder sound. See
[results](sound3-tone-lock-up-results.md). A post-observation literal model leads to
the next [minimum/maximum-return bitfield control](sound3-volume-lock-range-control.md),
registered before its data. No volume writer is enabled.
