# Sample memory limit: 241 pages, 987136 codes, 42.1 s

The [limit test](sample-memory-limit-control.md) offered exactly 241 pages of sample data
in a complete layout. The restore finished without ERR, and the backup equals the
compiled target exactly, including all 16 of Sound16's key references at the end of the
stream. The registered `limit_is_241_pages` hypothesis holds.

Pattern 1 played Sound16, the last kit in memory. In all five loops each step lands within
0.5 cents of +100 (k-1), step 1 sounds at 800 Hz, and every hit lasts 180.8 to 181.3 ms
against 181.3 ms.

Together with the [over-limit step](sample-memory-step4-results.md), which kept an exact
241-page prefix of a 249-page restore, this sets the PO-33's sample memory at **241 pages
of 4096 codes: 987136 codes, 42.1 s at 23437.5 Hz**. That is slightly more than the
advertised 40 s. A larger restore ends in ERR and keeps only the first 241 pages of the
stream.

The drum importer now defaults to this limit (`DEVICE_SAMPLE_LIMIT` in
`src/po33_re/sample_import.py`). The legacy Sound6 import path keeps its older, smaller
budget unless a caller passes the device limit.

- [Registration](../experiments/sample-memory-limit-registration-001.json)
- [Decision](../experiments/sample-memory-limit-decision-001.json)
- [Observation](../experiments/compiled-sample-memory-limit-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-sample-memory-limit-001/project.json`

The next [long melodic test](long-melodic-control.md) imports a 4.0 s melodic sample.
