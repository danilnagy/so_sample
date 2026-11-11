# Sample memory holds 675840 codes

The [sample-memory step](drum-memory-control.md) restored four new full drum kits into
Sound13 to Sound16. Total sample capacity rose from 266240 to 675840 codes, 28.8 s at
23437.5 Hz. The restore finished without ERR, and the backup equals the compiled target
exactly, every buffer included.

Pattern 1 played Sound16, the last kit written. In all five loops each step lands within
0.1 cents of +100 (k-1), and step 1 sounds at 800 Hz within 0.1 cents. The person heard
a rising run of 16 beeps.

The importers now take the total limit as a parameter. Their defaults stay at the
largest totals carried when each was verified; 675840 is now the largest total observed.

- [Registration](../experiments/drum-memory-registration-001.json)
- [Decision](../experiments/drum-memory-decision-001.json)
- [Observation](../experiments/compiled-drum-memory-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-drum-memory-001/project.json`

The [next step](sample-memory-step2-control.md) raises the total to 815104 codes.
