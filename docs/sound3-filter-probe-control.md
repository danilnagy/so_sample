# Sound3 FILTER selection before recording A

The current genuine project is the accepted generated14 body, with volume36 and
the established sample/note layout. Ordinary playback has already been recorded.
The first control now checks the resulting state after selecting FILTER while
leaving both knobs untouched.

## First physical action: selectionA

1. Keep both knobs and all audio settings unchanged. Stop playback and ensure write off.
2. Select Pattern1 / Sound3. Press FX until **FILTER** is selected, without moving
   either knob. The [official guide](https://teenage.engineering/guides/po-33/en),
   section6, describes FX as cycling the parameter modes.
3. Save a complete backup as
   `experiments/event-054-a-sound3-filter-selection/capture.wav` at the established
   reduced recording level with one second trailing silence.
4. Confirm FILTER is selected, then leave both knobs untouched. No restore or extra
   playback recording is needed. The recorded A pass waits for this capture to be
   verified; do not begin moving a knob yet.

The complete-body prediction for this control is
`05e1d379603f4457fd1496e516460e0a8de50cadf0fc810e9c2f3ca1da1b4637`.
The action includes already performed playback and the new selection. A difference
cannot be attributed to mode selection alone; it remains explicit and must be examined
before the recorded adjustment.

## Later, separately gated recordedB

Only after actual selectionA is verified, the later pass will record clockwise
movement of A in FILTER while B remains untouched. A is physically at minimum after
the earlier pitch controls, so an upward pass supplies movement without another
preparatory knob adjustment. Clockwise endpoint selection does not predict a cutoff
code, a filter type or audible direction.

The new strict location candidate is second-primary0xf0 plus third-primary0x03
in all16 Sound3/Pattern1 cells. A separate coupled alternative includes all of the
third byte, retaining possible simultaneous FILTER data. Broader Sound3 primary
and auxiliary changes and no serialized change are also registered. These remain
location hypotheses, not decoded cutoff/resonance fields or a declared field width.

Pitch, volume, sample data, other sounds/patterns, footer and packet geometry have
independent preservation/identity checks. B is compared with **actual A** even if
the selection prediction fails. A source hash recorded from actual A is a measured
source identity, not a fitted target prediction. Raw tuples, mixed values and all
wider changes remain visible. No endpoint value, frequency curve, resonance scale,
UI reading or uniformity is guessed. No public filter writer is enabled.

All37 affected FILTER/pitch tests pass, including no-change, mixed values, a coupled
third byte, unexpected pitch/volume/auxiliary data, hidden unrelated changes,
changed selection and refusal to widen registered masks. The full public-pitch
regression suite passed917 tests before these added FILTER controls.

- [Preregistration](../experiments/sound3-filter-selection-and-A-registration-001.json)
- [Accepted pitch14 source](generated-sound3-pitch-interval-results.md)
- [Checker](../scripts/check_sound3_filter_probe.py)

After independent selectionA decoding at threshold0.0063:
`python -m scripts.check_sound3_filter_probe --selection-only`.
The later two-capture analysis uses the same checker without that flag. Reports
remain software-only; hardware observations remain separate.

## SelectionA accepted; next physical action: recordedB

The complete selectionA body and all815 packets match the accepted generated14
project exactly. Existing ordinary playback and the confirmed FILTER selection leave
no stored change in this control. The user's "done and confirmed" is recorded as
confirmation of the requested selection, without inventing a label, numeric reading
or audible result. Pitch stays14 and volume36 in all16 cells; all other state is exact.

Backup peaks near0.150/0.144 remain suitable. All31 content hashes and full native
reconstruction pass for the current genuine read-only export:
`experiments/exported-sound3-filter-selection-001/project.json`.

- [Selection checks](../experiments/event-054-a-sound3-filter-selection/selection-results-001.json)
- [Separate hardware observation](../experiments/event-054-a-sound3-filter-selection/hardware-observation-001.json)
- [Recorded-pass handoff validation](../experiments/filter-selection-to-recorded-A-workflow-validation-001.json)

The recorded pass is now ready under the original masks and broader alternatives.
It uses actual selectionA as its measured baseline; no endpoint code is predicted.

1. Keep Pattern1 / Sound3 / FILTER selected, B and all audio settings unchanged.
2. Start Pattern1, hold WRITE, and slowly turn only A fully clockwise over about
   5 seconds. Hold WRITE 3 more seconds with both knobs stationary. Do not press
   keyboard keys or hold BPM/FX during the pass.
3. Release WRITE, stop playback and ensure write off. Save a full backup as
   `experiments/event-055-b-sound3-filter-A-lock-up/capture.wav` at the established
   reduced level with one second trailing silence.
4. Report any audible change and any display label/number actually observed;
   uncertainty and missing readings remain valid. Leave A at maximum and B untouched.
   No restore or separate ordinary playback recording is needed.

Cutoff/resonance location, width, numerical endpoint and a filter writer remain
unverified until the new physical data is analyzed.

Completed: recorded clockwise A changes only the strict candidate bits. All16
contiguous projections become62, while pitch14, volume36, other third-byte bits and
every unrelated field remain exact. The user reports high-pass filtering to an
inaudible sample and qualitative bar movement, without a numeric reading. See
[results](sound3-filter-A-clockwise-results.md) and the next
[opposite endpoint / exact clockwise return](sound3-filter-A-range-control.md).
