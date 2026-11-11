# How the PO-33 stores a drum recording

The [observation](drum11-record-observation-control.md) recorded 16 tone bursts into empty
drum Sound 11 on the device. One backup shows:

- **Ownership.** One new self-owned buffer under Sound 11's first slice id, 40, with a
  102400-code capacity (25 pages of 4096). The other 15 slice ids hold 9-byte references to it.
- **Trimmed start.** The stored audio begins at the first burst; the leading silence of the
  file and of the button press was dropped.
- **Onset slicing.** The 16 windows are consecutive but not equal (2765 to 3122 codes). Each
  boundary sits at a detected burst onset, within a few milliseconds, and slice k holds burst
  k: the dominant frequencies run 400.2, 436.3, 475.6 ... 1345.4 Hz in order.
- **Last slice to the end.** Slice 16 starts at the 16th burst and runs to the end of the
  recording, code 101824.
- **Nothing else changed.** Every other sound record and pattern cell is unchanged.

The registered "equal split" hypothesis fails; the other three hold. Total sample capacity
on the device is now 266240 codes, beyond the importer's conservative 172032-code budget,
with no reception problems; the budget is not a device limit.

See the [result](../experiments/drum11-record-result-001.json) and
[observation](../experiments/observe-drum11-record-001/hardware-observation-001.json).
Current genuine export: `experiments/exported-drum11-record-001/project.json`.
