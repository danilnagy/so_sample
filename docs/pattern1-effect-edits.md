# Guarded uniform Pattern1 effect plans

Schema-1 plans now accept:

```json
{"operation": "set_pattern1_effect", "effect": "octave_down"}
```

Allowed names are `none`, `octave_up` and `octave_down`, corresponding to uniform
footer nibbles15/6/7. Only the exact tested Pattern1 project context is supported:
normalizing its eight footer bytes to FF must reproduce clear body
`3d3762e28817a2bccf83986539c889d1e74e70139b2313affcc3d56cc1bb370b`.
This pins every sample, all sixteen patterns, every sound parameter and all
globals, including global131=7. Sources may use any of the three uniform known
effects. Mixed, unknown or differently configured projects are rejected.

APIs in `po33_re.formats.effects` are `calibrated_pattern1_effect(frame)` and
`set_calibrated_pattern1_effect(frame,effect)`. The setter changes only eight
Pattern1 footer bytes. Same-effect plans are exact no-ops. Integers, booleans,
lists, unknown names and extra plan arguments are rejected. This operation does
not support a step number, another pattern or arbitrary effect codes.

All three generated states have exact physical native reception. The earlier
recorded FX7 report explicitly confirmed octave-up with footer6/global9; the
generated footer6/global7 report confirms hearing the octave effect in that
requested context. Generated footer7/global7 is explicitly confirmed octave-down,
and footerF/global7 returns normal playback and the entire independent clear
baseline. No frequency ratio is inferred from those listening reports.

Public replay outputs are:

- `experiments/replay-pattern1-effect-octave_up-plan-001`
- `experiments/replay-pattern1-effect-octave_down-plan-001`
- `experiments/replay-pattern1-effect-none-plan-001`

Each compiled restore WAV equals the respective hardware-accepted WAV byte for
byte and reproduces the complete native body. Compile a plan bound to its own
source hashes with `python -m po33_re apply-edits ARTIFACT --plan PLAN --out-dir FRESH_DIRECTORY`.
The compiler retains `hardware_verified:false`; replaying an accepted file is
not a new physical restore. Earlier observations that record writer-disabled
status remain immutable snapshots of their creation time.

This is a uniform effect operation. Per-step nibble order, every effect code and
global131's meaning remain unknown. Other pitch/filter/resonance writers retain
their existing guards; no untested combined context is admitted here. All1,246
regression tests pass, followed by72 focused checks with no later production
changes.

- [Accepted down and clear](generated-pattern1-FX-return-results.md)
- [Accepted generated octave effect](generated-pattern1-FX-up-results.md)
- [Next mixed-effect control](generated-pattern1-FX-mixed-control.md)
