# Recorded octave-down followed by clearing effects

Current genuine state has footer6 throughout and global byte131=9 after recorded
FX7. The original footer-only model failed. New footer-plus-global alternatives
are registered before these two captures: global low-four mask0x0f and broader
whole-byte mask0xff, with every other byte preserved. Neither new global value is
predicted.

The [official guide](https://teenage.engineering/guides/po-33/en), section6, identifies
FX8 as octave-down and FX16 as no effect, used to clear saved effects in write mode.
Keep Pattern1 selected, both knobs and all recording settings unchanged.

1. With playback stopped, press WRITE once to enable write mode; leave WRITE
   released. Start playback and hold **FX + key8** for about8 seconds. Release them,
   immediately stop, and switch write mode off. Save the complete backup as
   `experiments/event-066-b-pattern1-FX8-recorded/capture.wav`.
2. Save the first backup before proceeding. Repeat the same write-mode/playback
   sequence, now holding **FX + key16** for about8 seconds to clear saved effects.
   Release them, immediately stop and switch write mode off. Save
   `experiments/event-067-c-pattern1-FX16-clear/capture.wav`.

Use the established reduced recording level and one second trailing silence for
both backups. Report the actual sound/display changes. No restore or separate
playback recording is required; do not move knobs or press other keyboard keys.

A new key-minus-one footer hypothesis predicts7 in all nibbles for FX8, then15
for clear. Those are hypotheses selected after observed FX7 code6, not already
decoded full-map facts. Mixed values, unchanged passes and failed predictions
remain literal. Both nibble orders are retained; uniform data cannot choose one.

Clear is predicted to reproduce the independent original no-FX state except the
explicitly unknown global byte131. Whole original-body equality is an additional
diagnostic, without guessing that byte will return0. Low-four and whole-byte
scopes remain distinct; a high-bit change cannot rescue the narrower model. Wider
primary/auxiliary, other-pattern, sample or other-global changes are not absorbed
into these scopes. No public FX writer is enabled.

- [Preregistration](../experiments/pattern1-FX8-clear-return-registration-001.json)
- [Original failed footer-only control](pattern1-FX7-results.md)
- [Checker](../scripts/check_pattern1_fx_return_controls.py)

After independently decoding both captures at threshold0.0063, run
`python -m scripts.check_pattern1_fx_return_controls`. Reports remain immutable
and hardware-unverified. All56 affected checks pass; production code is unchanged
since the full1,137-test run.

## Octave-down completed; clear input needs correction

The first capture passes footer7 and the footer/global low-four scope, with global
byte131=1 and all other state exact. The user reports lower octave then normal.
Both supplied WAVs are byte-identical copies of the octave-down recording, so the
clear comparison is not independent evidence. Preserve the original report/files
and supply the actual clear backup in the
[fresh corrected folder](pattern1-FX16-corrected-clear-control.md). See
[accepted first-leg results](pattern1-FX8-results.md).
