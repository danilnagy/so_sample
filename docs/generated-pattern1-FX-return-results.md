# Generated down and clear received exactly

Both physical WAVs are independent. At threshold0.0063 each recovers815
checksum-valid packets ending at156758 and matches every packet and the entire
preregistered target body.

| Leg | Footer | Global131 | Body | User confirmation |
| --- | --- | --- | --- | --- |
| Down | 77 eight bytes | 7 | 01cb7130... | Octave down |
| Clear | FF eight bytes | 7 | 3d3762e2... | Normal |

The user reports: "done and confirmed I heard octave down and normal". No
measured frequency ratio or numeric display report is added. Clear returns the
complete independent no-effect body from the accepted plain-playback capture,
including global131=7. This baseline is distinct from the earlier pre-FX state
whose global byte was0. All samples, notes, sound parameters and other globals
are preserved throughout this generated pair.

Both recordings are unclipped: down channel peaks0.15533/0.15051; clear peaks
0.15472/0.14948. The established reduced level remains suitable.

- [Frozen pair prediction](../experiments/pattern1-generated-FX7-clear-global7-registration-001.json)
- [Down native result](../experiments/edited-pattern1-FX7-global7-down-001/hardware-recapture-results-001.json)
- [Down hardware observation](../experiments/edited-pattern1-FX7-global7-down-001/hardware-observation-001.json)
- [Clear native result](../experiments/edited-pattern1-FX15-global7-clear-001/hardware-recapture-results-001.json)
- [Clear hardware observation](../experiments/edited-pattern1-FX15-global7-clear-001/hardware-observation-001.json)

Both new read-only exports have all31 content hashes and full native reconstruction
verified. Current genuine export:
`experiments/exported-pattern1-generated-FX15-global7-clear-001/project.json`.
All original software reports, predictions and observations remain immutable.

These results support [guarded uniform effect plans](pattern1-effect-edits.md) for
none/up/down in this exact project context. Global semantics and per-step nibble
order remain unknown. The next [mixed-effect control](generated-pattern1-FX-mixed-control.md)
tests combining both effects within one pattern. All1,246 regression tests pass,
followed by72 affected checks; production code remains unchanged after the full run.
