# First pattern event: controlled A/B/A

Status: user confirmed Pattern 1 is empty and Sound 9, slice key 1 is a recognizable kick. Ready for captures; none have been collected.
Default target is Pattern 1, Step 1, Sound slot 9, drum slice key 1. The target step must
be empty for the selected sound, and the slice should play a recognizable sound. If those
conditions are not met, choose another documented empty step and populated drum slice
before collecting A. Do not reset the device or clear an existing pattern for this experiment.
Keep the already verified backups unchanged.

## Capture setup

Use the same reduced recording level validated with reconstructed-002. Retain 44.1 kHz,
16-bit stereo PCM and processing disabled. Capture the complete transfer with a short lead-in
and tail. Store original recordings unchanged; keep a second copy. The analysis profile is
explicit threshold 0.0063, subject to checking each recording's measured level and noise.

Prepare the target UI state before A: stop playback, select only the target pattern and
sound, and audition the target slice while write mode is off. Do not create a pattern chain.
The official guide describes selecting a sound using sound + its slot key, selecting a
pattern using pattern + its key, and toggling write mode with write. In write mode, number
keys enter steps; pressing a lit step removes it. See sections 3-5 of
https://teenage.engineering/guides/po-33/en. Log the selected slice key explicitly rather
than inferring the event from sound-slot number alone.

## A: known state

Confirm the chosen step is empty before any edit. Keep the selected pattern, sound, last
slice key, tempo, swing, parameters and pattern chain documented. Write mode must be off
and playback stopped for every capture. Record A to:

`experiments/event-001-a/capture.wav`

A is a new experiment baseline after selecting the target UI state, not assumed equal to
the older baseline-002 state. Existing unrelated events/samples may stay as they are.

## B: one added event

Enter write mode and add one trigger at the chosen step using the selected sound and
slice. Exit write mode. Do not adjust knobs, effects, tempo, slices, chain, or other steps.
Keep the same selected UI state and playback stopped; do not audition the pattern between
captures. Record B to:

`experiments/event-001-b/capture.wav`

If editing requires selecting or auditioning another note/slice, log that action and restore
the same target selection before recording. No intentionally recorded effects or parameter
locks should be introduced. Record any accidental or unexpected changes.

## A again: remove the event

Enter write mode, remove only the trigger just added, confirm that step is empty again,
and exit write mode. Keep the same selected pattern/sound/slice and playback stopped.
Record the return capture to:

`experiments/event-001-a-return/capture.wav`

Use the step indicator to verify the edit; postpone listening/playback until all three
captures are collected so the action path is controlled. Confirm return to baseline behavior
and log any controls used for that check separately from the capture sequence.

## Action record and analysis

Each folder contains experiment.json with separate planned and observed values/actions.
Fill actual actions and observations; proposed state is not evidence of device state.
Note the exact pattern, step, sound slot and slice key, selected UI state, pattern sequence,
recording interface/settings and any unusual receive/transmit behavior. Keep timestamps
unknown until observed. The series manifest is experiments/event-001-series.json.

Analyze A versus returned A first. If they do not match in a justified representation,
investigate return-state and decoding variation before attributing B differences to the event.
Compare both channels independently and retain exact counts and endpoint differences.
Absolute labels, phase transitions and any future framed payload remain distinct representations.
Large difference regions may reflect coding, serialized UI state, or alignment; they do not
identify a pattern field by themselves. No offset or checksum is assumed.

After a repeatable hypothesis emerges, confirm with independent positions and values.
Writable fields require successful controlled restoration; one A/B/A series does not confirm
an editable pattern representation. The field map starts empty pending those observations.
