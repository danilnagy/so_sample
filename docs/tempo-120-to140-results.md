# The first tempo-byte prediction matches the device

The user reported **done, changed from 120 to 140**. These display values were supplied
independently of the backup bytes. The capture passes all 815 native checksums at the
established threshold 0.0063, retaining frame end byte 156758 and all packet tags/sizes.

Exactly one plain payload byte changes: offset 129 (zero-based) in the second `0x7d5c`
packet, at native packet index 2, changes 120 to 140. Every other plain packet byte, sample
record, pattern and selector remains unchanged. The first opaque global record is exact.
This supports the preregistered direct integer BPM hypothesis for this transition,
without refitting the candidate offset or changing the decoder.

This physical association is recorded separately from writable-field validation.
Independent values, an exact return control and a generated restore still matter.
No tempo writer, arbitrary tempo range or generated tempo-edit hardware acceptance is
claimed. The read-only project preserves both global records literally.

- [Native comparison](../experiments/event-030-b-tempo-preset-once/native-tempo-results-001.json)
- [Independent user observation](../experiments/event-030-b-tempo-preset-once/manual-observation.json)
- [Hardware association and limits](../experiments/event-030-b-tempo-preset-once/hardware-observation-001.json)
- Current read-only project: `experiments/exported-tempo-140-001/project.json`
- Capture SHA-256: `cedcdd9b97674b93b3ebb623e3ebd2744ddb4f188a9fd899eac9407903efc1ef`
- Artifact SHA-256: `b6d4e617213811f5bdcfabe389172989bda3d30eaf3a38923adcc0bde1891690`
- Native body SHA-256: `e842aaea00d667ad6ef325a2e8cd870baa5e92dda7c7b3912270b41f740ba4df`

All 31 exported content hashes and the reconstructed complete body pass. Capture peaks
are about 0.164 and 0.158 without clipping. The next
[third-preset and return control](tempo-preset-series-control.md) is registered before
both captures: 140 to 80, then 80 to 120, with the whole return body expected to equal the
independent original 120 backup.
