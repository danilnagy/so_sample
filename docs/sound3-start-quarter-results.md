# Second start observed; a separate endpoint test is ready

The quarter-position capture passes all preservation checks and all **511 checksums**
using the normal crossing decoder at threshold0.0063. Sound3 stores
**start11716, endpoint11827, owner0**, reference **c42d0000332e000000**.
Only bytes0/1/4/5 of reference packet375 change. The65536 backing codes, other sounds,
all16 patterns and every unrelated packet remain identical to the registered baseline.

The positive lower-start prediction passes. Both registered second-field predictions,
unchanged39393 and reset65535, fail and remain recorded as failures. The observed width
**111** matches the earlier physical minimum at start31393. With knobB physically at
minimum but untouched, automatic endpoint coupling is plausible; this control does not
isolate knobB or establish a general minimum rule. No audition was requested here.

- [Original predictions](../experiments/sound3-start-quarter-predictions-001.json)
- [Preservation and separate hypothesis results](../experiments/sound3-start-quarter-results-001.json)
- WAV SHA-256: `77ff3658428a7de39ebaca89005c2d88977cee24c7b841cab6fe8f6d344b7d24`
- Artifact SHA-256: `e0563dce21423d54daf1535e98afeeff72e75cf8415fac1ae37315b52e713417`
- Native body SHA-256: `bdd3c2d38d525c2a098994939b22816db959a2555b292740b7e816b4ee7b62e6`
- Stereo PCM16/44100Hz,1125431frames/25.520seconds; peaks0.16714/0.15994, no clipping indicators.

The next candidate retains start11716 and changes endpoint11827 to **19716**, selecting
8000 codes under an explicit half-open preview convention. It changes only bytes4/5 in
the same reference packet. The source is hash-pinned; all unrelated native packets are
preserved, the inverse reproduces the entire source body, and the generated stereo WAV
passes strict phase/count and complete native-body roundtrips.

This candidate lives in a separate experimental script accepting only these two endpoint
values at the exact second-start reference. **Public writers, edit plans and calibrated
project previews retain their existing start31393 scope.** Hardware verification of the
new candidate is pending; no arbitrary start, interpolation, general minimum-width rule
or device endpoint inclusivity is enabled. See the
[second-start restore test](native-quarter-window-restore-test.md).

The complete suite passes **346 tests in57.98seconds**, with Ruff lint and formatting
checks passing for all110Python files. New checks retain both failed endpoint hypotheses,
reject checksum-valid backing changes, enforce the isolated candidate's endpoint scope,
confirm that the public writer still rejects this start, and reproduce the registered WAV
without allowing existing outputs to be overwritten.
