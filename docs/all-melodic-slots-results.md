# Imports verified in all eight melodic slots

The [all-melodic-slots test](all-melodic-slots-control.md) gave every melodic slot its own
buffer. The backup equals the compiled target exactly:

- **Sound2, Sound3 and Sound8**, which borrowed Sound1's buffer, each own a new buffer
  under their own sound id.
- **Sound1**, once nothing referenced it, holds a new buffer.
- **Sound4 to Sound7** were replaced, and **Sound9 and Sound10** hold small kits of their own.

Pattern 1 played Sound s on step 2s-1. In all five loops every step lands within 0.2 cents
of 150 (s-1) cents above step 1, and step 1 sounds at 599.25 Hz against 599.3 Hz. The
person heard eight rising notes.

So melodic slot s is sound id s-1 for every slot. With `replace_borrowed`, the melodic
importer can write any slot whose buffer is borrowed, once it is no longer lent out.

- [Registration](../experiments/all-melodic-slots-registration-001.json)
- [Decision](../experiments/all-melodic-slots-decision-001.json)
- [Observation](../experiments/compiled-all-melodic-slots-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-all-melodic-slots-001/project.json`

The next [selected-pattern test](selected-pattern-control.md) writes Pattern 5 and
selects it.
