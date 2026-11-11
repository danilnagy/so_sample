# Generated octave-down then clear with global131 fixed

The accepted generated footer6/global7 state supplies the exact source. Two new
restores change only the eight Pattern1 footer bytes, keeping global131 at7 and
preserving all other state. Both predictions are registered before either new
physical recapture. The second software target already equals the entire
independent clear baseline, including that global byte.

Do these in order. For each restore, save the backup **before listening playback**,
then briefly play Pattern1 with write off and stop. Leave both knobs untouched,
do not press FX, and use the established restore and reduced recording levels.
Keep one second of trailing silence in each complete backup.

| Order | Restore WAV | Save backup in same folder as | Listening check |
| --- | --- | --- | --- |
| 1 | `experiments/edited-pattern1-FX7-global7-down-001/restore.wav` | `capture.wav` | Octave lower |
| 2 | `experiments/edited-pattern1-FX15-global7-clear-001/restore.wav` | `capture.wav` | Normal pitch, effect cleared |

Folder numbers6/7/15 describe the raw footer nibble values. They are not PO-33
button numbers; this generated clear requires no physical FX16 action.
No separate ordinary playback recording is needed. Report what you hear for each
restore, including uncertainty. Both captures may be uploaded together in order.

| Leg | Fixed source body | Fixed target body | Footer | Global131 |
| --- | --- | --- | --- | --- |
| Down | 1147b3d4... | 01cb7130... | 77 eight bytes | 7 |
| Clear | 01cb7130... | 3d3762e2... | FF eight bytes | 7 |

The constructor allows only these exact source bodies and fixed research legs.
Both44.1kHz stereo PCM16 waveforms at amplitude0.5 pass strict phase and full native
body/packet roundtrips. The generated clear body exactly equals the independent
accepted plain-playback clear state. These are software checks; physical restore
and listening remain pending.

- [Frozen pair registration](../experiments/pattern1-generated-FX7-clear-global7-registration-001.json)
- [Preparation](../scripts/prepare_generated_pattern1_fx_return.py)
- [Recapture checker](../scripts/check_generated_pattern1_fx_return.py)
- [Accepted generated octave-effect source](generated-pattern1-FX-up-results.md)

Decode each physical capture independently at threshold0.0063 into its respective
`derived/analysis-001` directory. Run
`python -m scripts.check_generated_pattern1_fx_return --leg down` first, then
`python -m scripts.check_generated_pattern1_fx_return --leg clear`.
The second checker requires a successful exact down result bound to its actual
WAV/artifact hashes and this registration. Every packet and the complete target
body must match; clear must also equal the independent baseline in full.
Copied inputs and any hidden global, note or sample change fail. Preserve any
failed prediction without expanding its scope.

Native reception and listening are distinct. Even success does not resolve
per-step nibble order, every effect code or global131 semantics. No public FX
writer is enabled. All74 affected checks pass; production code is unchanged since
the full1,137-test run.

## Completed

Both captures match their complete targets; clear exactly returns the independent
global7 baseline. The user explicitly confirms octave-down then normal. See
[results](generated-pattern1-FX-return-results.md). The evidence now supports
[uniform effect plans](pattern1-effect-edits.md) in the exact tested project,
with a separately preregistered [mixed-effect test](generated-pattern1-FX-mixed-control.md)
pending. Original registration/software status is retained unchanged.
