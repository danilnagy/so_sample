# Past the limit: the device keeps a 241-page prefix

The [over-limit step](sample-memory-step4-control.md) offered 1019904 codes of samples,
249 pages of 4096 codes, 43.5 s. The PO-33 showed ERR a little over 4 minutes into the
4.5-minute restore. The registered `advertised_limit_rejects` hypothesis holds; the
outcome class is `other`.

The backup shows exactly what the device kept: an exact prefix of the restore stream.

- **Kept intact:** every pattern, all sample buffers before Sound16 including Sound10's
  new kit, and the first 69632 codes of Sound16's buffer. Each matches the target byte
  for byte.
- **Dropped:** the rest of Sound16's buffer and its 15 key references, sound ids 121
  to 135. Sound16 keeps only key 1's window.
- **Stored total:** 987136 codes, exactly 241 pages, 42.1 s at 23437.5 Hz.

Patterns travel before the sample data, so they survive an overflow. The cut falls on a
page boundary. An exploratory reading of the playback, not registered, shows Sound10
playing all 16 keys within 0.3 cents of +100 (k-1) and step 1 at 350.0 Hz.

The working hypothesis is a limit of 241 pages of sample data, about 42.1 s, slightly
above the advertised 40 s. The [limit test](sample-memory-limit-control.md) offers
exactly 241 pages in a complete layout.

- [Registration](../experiments/sample-memory-registration-004.json)
- [Decision](../experiments/sample-memory-decision-004.json)
- [Observation](../experiments/compiled-sample-memory-004/hardware-observation-001.json)
- Export of the truncated device state: `experiments/exported-sample-memory-004/project.json`
