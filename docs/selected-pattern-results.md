# Pattern 5 written and selected through global byte 0

The [selected-pattern test](selected-pattern-control.md) copied Pattern 1 to Pattern 5,
reversed Pattern 5's notes and set byte 0 of the second global record to 4. The backup
equals the compiled target exactly. The person pressed only play and heard eight falling
notes.

In all five loops every step lands within 0.3 cents of `pattern5_selected`, and step 1
sounds at 1099.3 Hz against 1099.1 Hz. `pattern1_plays` fails.

So:

- **Byte 0** of the second global record is the selected pattern, counted from zero, and
  the device plays that pattern after a restore.
- **The pattern writers** work outside Pattern 1. `copy_pattern`, `set_melodic_notes` on
  Pattern 5 and `set_selected_pattern` are hardware verified.

- [Registration](../experiments/selected-pattern-registration-001.json)
- [Decision](../experiments/selected-pattern-decision-001.json)
- [Observation](../experiments/compiled-selected-pattern-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-selected-pattern-001/project.json`

The next [chain observation](pattern-chain-control.md) records how the device stores a
chain of Pattern 1 and Pattern 5.
