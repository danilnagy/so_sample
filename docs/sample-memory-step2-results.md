# Sample memory holds 815104 codes

The [second memory step](sample-memory-step2-control.md) passed every registered check.
The backup equals the compiled target exactly: Sound11 and Sound12 in full 102400-code
buffers, and a new 1.2 s tone in Sound6. Total sample capacity is 815104 codes, 34.8 s.

Pattern 1 played Sound11 again. In all five loops each step lands within 0.3 cents of
-100 (k-1), step 1 sounds at 1500 Hz within 0.5 cents, and each hit stops at its window
end within 0.6 ms.

**Battery loss during the first run.** The batteries died between the restore and the
backup. The backup taken after fresh batteries was a valid but empty 18 KB backup: no
sample buffers and no pattern notes. The device returned to an empty state rather than
keeping either the old or the new contents. A second full session then passed. The empty
backup is kept in the session archive, `attempts/session-001-accepted`. Keep batteries
fresh before long restores.

- [Registration](../experiments/sample-memory-registration-002.json)
- [Decision](../experiments/sample-memory-decision-002.json)
- [Observation](../experiments/compiled-sample-memory-002/hardware-observation-001.json)
- Current genuine export: `experiments/exported-sample-memory-002/project.json`

The [next step](sample-memory-step3-control.md) raises the total to 917504 codes.
