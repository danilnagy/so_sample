# Sample memory holds 917504 codes

The [third memory step](sample-memory-step3-control.md) passed every registered check.
Total sample capacity is 917504 codes, 39.1 s of the advertised 40 s. The backup equals
the compiled target exactly:

- **Sound9** holds its own 102400-code kit, owned by sound id 8, where its keys used to
  borrow windows of Sound1's buffer.
- **Sound1's buffer** and Sound10's references into it are unchanged.

Pattern 1 played Sound9. In all five loops each step lands within 0.1 cents of
+100 (k-1), and step 1 sounds at 450 Hz within 0.1 cents.

The drum importer can therefore give any drum slot its own kit, whether the slot was
empty, already self-owned, or borrowing another sound's buffer.

- [Registration](../experiments/sample-memory-registration-003.json)
- [Decision](../experiments/sample-memory-decision-003.json)
- [Observation](../experiments/compiled-sample-memory-003/hardware-observation-001.json)
- Current genuine export: `experiments/exported-sample-memory-003/project.json`

The [next step](sample-memory-step4-control.md) goes past the advertised limit.
