# Web app playback

The app previews a pattern or the song chain through the browser's audio output. It is
built on the measured laws, so pitch, level, filter, timing and the four-voice rule
match the device as far as they have been measured. It is a preview, not an emulation:
the punch-in effects are not reproduced, and the filter's shape between its measured
edges is the browser's biquad.

## Transport

Play and Stop in the status bar, or Space when no control has the keyboard. Song mode,
the default, walks the chain and marks the pattern sounding in the bar. Pattern mode loops
the pattern selected in the bar and follows a change of selection at the next bar. The step
sounding carries a 1px ring in the grid while the pattern on screen is the one sounding.
Edits take effect at the next bar; switching projects stops the preview.

## What is reproduced, and from where

| Behaviour | Source |
| --- | --- |
| Sixteen steps to a bar of four beats at the tempo; even steps delayed by swing/24 of a step | [swing law](swing-law-results.md) |
| A note takes its sound's held parameters: the last lock on any earlier step or bar, starting from pitch 13, volume 36, filter 63, resonance 1 | [no lock](no-lock-results.md), [volume law](volume-law-results.md) |
| Melodic keys transpose by the measured intervals from key 5; the pitch code adds one semitone per code around 13, on melodic and drum sounds | [key scale](pattern1-key-scale-map-results.md), [pitch law](pitch-law-results.md), [drum pitch](drum-pitch-results.md) |
| A pitch change glides from the previous pitch over 30 ms; key changes do not glide | [pitch law](pitch-law-results.md), [bit 5](bit5-glide-results.md) |
| Volume from the measured gain table, 0 dB at code 36 | [volume law](volume-law-results.md) |
| Filter: codes 1 to 31 low-pass and 44 to 62 high-pass at the fitted edges, flat at 0, 32 to 43 and 63; resonance sets the peak at the edge from the eight measured levels | [filter law](filter-law-results.md), [resonance law](resonance-law-results.md) |
| Four voices, taken in the measured sound priority; a sounding note is never cut; a voice takes a new note when free or within 100 ms of its end, and the rest of the step's notes are dropped | [priority](priority-map-results.md), [stealing](voice-steal-results.md), [release](voice-release-results.md) |
| A melodic note's length: cut after n steps, F plays the whole sample; a drum note's retriggers: n hits a step/n apart on the note's one voice, each restarting the sample | [aux nibble](aux-nibble-results.md), [aux nibble 2](aux-nibble-2-results.md) |
| Under swing, a note's time ends on the unswung grid: a delayed melodic note loses the delay, a delayed drum step plays only the repeats before the next step's grid line (exploratory, one session) | [aux nibble 3](aux-nibble-3-results.md) |

## Narrow screens

Below 840px, where the sequencer no longer fits, the app shows a pad layout with a view
bar (Sound, FX, Pattern, Song) and, under it in every view, the pattern strip (the
desktop bar's sixteen buttons, one row or two of eight). Sound, the view the app opens
on, is the sequencer's first column (number, icon, name, shape) with, at the right, a play
button (the desktop's appears on hover, which touch lacks) that a monitor covers while the
sound plays, from the preview or from an audition, showing the key for as long as the
sound lasts without taking the tap, and the mute and solo buttons; tapping a header opens
its editor and makes it the sound the Pattern view sequences. FX and Pattern show a
context row for the view's own controls and one 4x4 pad grid in the device's key layout.
FX puts the effects of the current pattern on the pads, and its bar holds Copy and Clear
for the whole pattern at the left and for its effects at the right, wrapping onto two
lines on the narrowest screens (a copy is finished by tapping a pattern in the strip); Pattern puts the chosen sound's steps there, with a row of sixteen keys above
that shows the sound's current key and changes and auditions it. A tap on a blank step adds a note and selects the step; a tap on
another note selects it; a tap on the selected note removes it; a press anywhere else
drops the selection. The selected step is outlined. A parameter row under the keys,
disabled while no step is selected, holds a list of the four step parameters and a slider
with the step's value (its own lock, else the one carried from the last lock before it,
else the default). Clear removes the step's lock on the chosen parameter and Clear all
removes all four, as a double-click on a desktop lane handle does: the code becomes 0 and
the step holds the last lock before it. Song lists the song's entries as rows, like the
sounds: a handle at the left drags a row to a new place, a tap on the entry selects it, and
buttons at the right move it up or down or remove it; an Add pattern row at the end opens
the pattern picker. On the desktop a click on a song chip selects it and Move left, Move
right and Remove appear beside Clear; chips drag to reorder as well.

The dot on a step, in the sequencer, the rolls and the pads, marks a lock that changes a
parameter: a nonzero code that differs from the value held before the step, the last lock
before it round the pattern. The device records the knob positions with every note, so a
note that repeats the held values has no dot, and a step whose locks are removed loses it.

Playback and following work as on the desktop. The markers sit under the pads, their top
edge on the pad's bottom edge, in FX and Pattern for the sounding step only while the
pattern shown is the one playing (otherwise the pattern strip
above points at it). The sounding song entry carries a marker at its row's left edge, and a long song
scrolls under the bars, which stay put. The modals are shared with the desktop layout. The bottom bar is one row at every width:
on a phone tempo and swing fold into one button that opens steppers, the memory meter
drops its words, and under 480px the transport buttons show a stop square and the letters P, S and F instead of words. Follow stays in place in pattern mode, disabled. There
is no status line: notices appear as a toast over the bar, gone on a tap or after a few
seconds; the four-voice warning sits as a glyph on the pattern buttons and on the steps
whose notes are dropped, with its words on hover or on a tap; and the memory meter itself
turns to the warning style when the project outgrows the device. The top bar's theme list
becomes one button that cycles System, Light and Dark.

Each sound has a current key, saved with the project: 5 for a melodic sound and 1 for a
drum until changed. A new note programmed from a blank step, on the desktop or on the
pads, takes it, and the sound's play button plays it (a drum's play button plays the kit's
sample on that key). The key strip on a phone sets it, and so does any key programmed in a
roll: the last key programmed is the current one, and so does a tap on a filled pad in
the kit editor, where the current key is the filled pad and a dot marks a key the current
pattern plays.

## Mute and solo

Every sound row and every key of a drum kit has M and S buttons. They act on the preview
only: a muted note is scheduled silent but still takes its voice, so the four-voice
drops stay as the device would play them, and a solo anywhere silences everything not
soloed at that level. They are saved with the project and never written to a restore;
the device has no such state.

## Approximations

- The filter between its edge and the passband follows the biquad's slope, not a
  measured curve; the measured responses are in the filter-law measurements.
- Resonance is applied as the biquad's peak at the edge. The device also lowers the
  passband at low levels, which is not reproduced.
- Output level: one voice at volume 63 reaches full scale and a limiter catches the sum
  of four. The device's absolute level was not measured.
- A drum key with no sample is silent and takes no voice; whether the device reserves a
  voice for it was not measured.
- Note length and retrigger under swing follow a rule fitted to one session at 120 BPM and
  swing 12 ([aux nibble 3](aux-nibble-3-results.md)); other tempos and swing values, and
  their interplay with the effects, are not yet measured. A cut note or repeat fades over
  4 ms; the device's own cut was not measured.

## Code

`web/src/app/playback.ts` turns a project into timed note events for one bar and keeps
the per-sound and per-voice state between bars; it is pure and tested. `player.ts`
schedules the events on Web Audio a bar at a time, 200 ms ahead, and reports the
position for the cursor.
