# Nonzero-start drum edit verified on hardware

The clean retry matches the entire registered key2 target with **527 valid checksums**
and exact native re-encoding. Sound9/key2 retains **start4045, owner0** and stores
**endpoint6045**, reference `cd0f00009d17000000`. Only bytes4/5 of packet385 differ
from its minimum source. The accepted key1 endpoint2000, other14 references, every
backing code, melodic sound, pattern and unrelated packet remain unchanged.

The user previously confirmed restore and both requested Sound9 tones, then supplied
the updated recording. Normal crossing decode at0.0063 succeeds directly. This accepts
the registered local nonzero-start endpoint edit. Arbitrary starts, other drum keys,
sound slots, universal minima and exact hardware endpoint inclusivity remain unresolved.

- [Hardware validation](../experiments/edited-drum9-key2-end-001/hardware-validation.json)
- Clean retry WAV SHA-256: `447b8e92224fd5db41f53bb283bff66317da14a32bf9b0004669aed057cfec91`
- Artifact SHA-256: `0d8a5a3d61b1ec84848ad9fe45bf315c9aac7b9774420356ed455b9aefb0dd5b`
- Native body SHA-256: `1f3295c4cc8150d75a1513c76d996c54ed460c9b9d26730c556d7da24065ad28`
- Stereo PCM16/44100Hz,1095885frames/24.85seconds; peaks0.16861/0.16107, no clipping indicators.

The first recapture failed the crossing and clock decoders. Its exact WAV remains at
`capture-attempt-001.wav`, SHA-2565cfdffdf..., alongside its artifact, diagnostics and
historical failure report. The user replaced `capture.wav` with the clean retry, which
was copied to `capture-retry.wav`. Acceptance is recorded in a separate new report;
the failed attempt and software-only compiler/candidate reports are unchanged. The
cause of the first recording's errors remains unidentified.

With **--calibrated-drum-slices**, project export now previews both **Sound9 keys1/2**
in their local fixed-start context. Default exports still produce no drum audio previews.
The current export is **experiments/exported-verified-drum9-slices-001/project.json**:
all16 patterns, four melodic previews, and `samples/09-slice-01.wav` plus
`samples/09-slice-02.wav`. Each drum preview contains4096FLOAT mono frames at48kHz,
using explicit half-open2000-code selections without keyboard pitch or gain changes.
The other14 slices and all other drum slots remain raw/unpreviewed.

All28 exported content hashes and the complete native packet representation have been
checked. `preview_drum_slices` lists the two sound/key/file mappings separately from
the melodic preview list; the report version is read-only-project-export-0.5. The export
itself remains software-only, with hardware evidence recorded separately above.

The complete suite passes **409 tests in90.01seconds**, with lint/format checks passing
for125Python files. New regressions verify the genuine whole target, reject checksum-valid
changes to either accepted endpoint, require preview opt-in and validate both unscaled
preview waveforms while preserving source/native data. No blanket hardware claim is
made for every possible two-slice combination.

The next [Sound10 copy control](drum10-copy-control.md) tests another inferred drum block
while preserving both accepted Sound9 slices and all existing state.
