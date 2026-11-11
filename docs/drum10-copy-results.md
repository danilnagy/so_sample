# Second drum block and fresh-copy records verified

The clean retry passes every registered preservation check and all **543 checksums**
with the normal crossing decoder at0.0063. Only data under selector IDs **24..39** is
added, independently locating **Sound10's sixteen-record block**. Both accepted Sound9
windows, all backing codes, melodic records, patterns, selector order and unrelated
packets remain identical to the baseline.

Every separate prediction passes: all16 groups populate, each has one9-byte owner0
reference, the raw records match the **original Sound9 autocopy before its later edits**,
and exactly16 packets/224 body bytes are added. This copy adds references rather than
a new owned sample buffer. Individual Sound10 keyboard order, other allocation behavior
and a universal autoslice formula are not established by these results.

- [Original predictions](../experiments/drum10-copy-predictions-001.json)
- [Preservation, exact record comparisons and hypotheses](../experiments/drum10-copy-results-001.json)
- Retry WAV SHA-256: `073011e3cdd30f3bb376396385a154ec581d24412c0f93362d189e2e8126e804`
- Artifact SHA-256: `4ad498dd37a011e7dc30890d18b8416b412651b8aa3eecb7958fccf32252d1d4`
- Native body SHA-256: `9e2801c1d2e76144a88ea71c05cc69e0be58476d077305abb4997c2fb9d64323`
- Frame end89844,543 packets; stereo PCM16/44100Hz,1156743frames/26.23seconds.
- Peaks0.16840/0.16116, no clipping indicators.

The first recording failed late in the transfer, with a waveform timing discontinuity
and four identical consecutive stereo frames. Fixed clock-window and deterministic
repeat-removal diagnostics did not recover a valid frame. The original WAV, failed
artifact and all diagnostic derivatives remain preserved. Only the clean retry evaluates
the copy hypotheses. No diagnostic repair or expected bytes were used in its decoding.
The specific cause of the first discontinuity remains unidentified.

The sound view now groups selector24..39 as **observed Sound10**, retaining all144
reference bytes. Its keyboard keys remain candidates; Sound11..16 block mappings remain
unverified. Sound10 writing and audio preview are disabled until a direct slice control
provides more evidence. The current export is
**experiments/exported-drum10-copy-002/project.json**, containing all16 patterns, both
raw drum blocks, four melodic previews and the two calibrated Sound9 previews.

The first full-suite run exposed a pre-existing preview-header issue: identical shared
audio could receive different libsndfile PEAK timestamps when encoding crossed a second.
Export now reuses encoded bytes for identical mono preview arrays **within one export**.
The alias previews therefore match byte for byte while their audio remains unchanged.
This does not promise timestamp-independent preview hashes across separate exports.
An end-to-end regression deliberately crosses timestamp boundaries. The earlier export
is retained, and the refreshed export above uses the cache.

After this fix, the full suite passes **416 tests in67.04seconds**. Ruff lint/format
checks pass for127Python files. New tests verify exact copy predictions and preserved
state, keep boundary equality separate from locality, reject checksum-valid unrelated
changes and check that all16 Sound10 records remain raw without speculative audio.

The next [single-slice copy control](cross-drum-slice-copy-control.md) copies last-triggered
Sound9/key1 into Sound10/key1, testing its destination mapping and exact raw reference
copy while leaving every other source/neighbor unchanged.
