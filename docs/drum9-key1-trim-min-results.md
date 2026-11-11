# Drum key1 is localized; its minimum differs from the melodic prediction

The capture passes every registered preservation check and all **527 checksums** with
the normal crossing decoder at0.0063. Only **selector8 / packet383** changes after
Sound9 key1 is triggered and knobB moved to minimum. The first field stays **0**, owner
stays0 and the second field changes **4044→127**. Its raw reference becomes
`000000007f00000000`. Only payload bytes4/5 change; all other slices, sample codes,
melodic records, patterns and unrelated packets remain identical.

The key1/selector8 mapping, unchanged-zero first field and lower-second-field predictions
pass. The exact minimum **79** transferred from the earlier melodic control **fails**.
The observed127 is retained as a separate result, without rewriting the prediction or
declaring a universal drum minimum. No first-field coupling is observed in this control.

- [Original predictions](../experiments/drum9-key1-trim-min-predictions-001.json)
- [Preservation and separately evaluated hypotheses](../experiments/drum9-key1-trim-min-results-001.json)
- WAV SHA-256: `bb5cbcd9cee52cd390dcc9f5e33f1fec719891d951d4d92ae21d3dae1a924046`
- Artifact SHA-256: `3495d30f8003b614a828d94d6fba85a3c8fdef3e52a70f4b201c40a3c3153daf`
- Native body SHA-256: `ce8c3712bf6557ab0ea5a97363a7f9dbb35fba2293c670873a474f3e357cabc9`
- Stereo PCM16/44100Hz,1079157frames/24.471seconds, peaks0.16782/0.16064 with no clipping indicators.

The sound view now marks Sound9/key1 as directly observed; other keyboard positions remain
candidates. The current read-only export is **experiments/exported-drum9-key1-min-001/project.json**.
It retains all16 raw references, all16 patterns and four melodic previews. Drum previews
remain disabled in the exporter.

An experimental `set-drum-slice-end` writer now accepts only **Sound9/key1**, zero start,
owner0 with65536 backing codes and endpoints in the local **127..4044** interval. It
requires the exact other15 reference records observed in the Sound9 copy. Other keys,
sound slots, ownership/layout changes, altered neighbors and out-of-range endpoints are
rejected. The literal neighboring references are calibration data rather than a general
autoslice formula. The writer reproduces both complete genuine minimum/copy bodies and
their inverse. General drum minima, nonzero-start semantics and exact endpoint inclusivity
remain unresolved. Interior endpoint edits require appropriate hardware validation.

The first candidate sets endpoint **2000**, changing only two bytes of the calibrated
reference. Its hash-bound edit plan compiles through the bounded writer and passes full
phase/count, native-body and exact packet roundtrips. The candidate inverse reproduces
the entire minimum body. All unrelated native data stays intact. A separate preview reads
raw codes[0:2000] under the explicit half-open convention, without pitch or gain changes,
resampled to4096FLOAT mono frames at48kHz. It is not a data-transfer WAV.

The **first generated drum edit is not hardware verified yet**. See the
[restore test](native-drum9-slice-end-restore-test.md),
[software checks](../experiments/generated-drum9-slice-end-001/software-validation.json)
and [edit plan](../experiments/drum9-slice-end-plan-001/plan.json). The earlier physical
control report remains unchanged with its writer-disabled status at the time it was written.

The full suite passes **387 tests in63.48seconds**. Ruff lint and formatting checks pass
for118Python files. Tests retain the failed79 prediction, verify genuine forward/inverse
bodies and unknown-packet preservation, reject unsupported slice contexts and types,
exercise CLI source protection and reproduce the complete candidate pipeline.
