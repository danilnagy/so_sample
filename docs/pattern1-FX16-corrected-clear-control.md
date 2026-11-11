# Supply the actual clear backup in a fresh folder

The original FX8 and clear capture.wav files are byte-identical. Octave-down is
verified, but the actual clear recording is missing from the supplied data.
Preserve the original files and put the actual FX16-clear backup as
`experiments/event-068-d-pattern1-FX16-clear-corrected/capture.wav`.

If the original clear recording is unavailable, record a fresh complete backup of
the already-cleared device. Keep playback stopped, write off, both knobs and audio
settings unchanged. Use the established reduced level with one second trailing
silence. No repeat FX pass, restore or separate playback recording is required.

The original clear prediction remains footerFF and the independent pre-FX state
apart from the explicitly unknown global byte131. Low-four and whole-byte scopes
stay separate. Entire original-body equality remains a diagnostic, not a predicted
new global value. The corrected-input binding is created after the user reported
the physical clear action and before corrected data becomes available; the earlier
prediction itself was registered before that action.

The checker rejects the known duplicated raw-WAV hash before judging the clear
state. A genuinely different recording with unchanged decoded state is retained
as actual negative evidence instead of being confused with a duplicate file.
No field map, global role or FX writer is inferred from the input problem.

- [Correction identity binding](../experiments/pattern1-FX16-corrected-clear-registration-001.json)
- [Duplicate-input observation](../experiments/pattern1-FX8-clear-input-identity-observation-001.json)
- [Accepted octave-down and data issue](pattern1-FX8-results.md)
- [Checker](../scripts/check_pattern1_fx_corrected_clear.py)

After independent threshold0.0063 decoding, run
`python -m scripts.check_pattern1_fx_corrected_clear`. Output is immutable and
hardware-unverified. All34 affected checks pass; production code is unchanged
since the full1,137-test run.

## Completed with independent corrected input

The distinct corrected WAV recovers815 checksum-valid packets ending at156758.
The original FF footer prediction passes, as does the registered low-four scope.
Every byte of the independent original no-FX state returns except global131,
which is7. Entire original-body equality is therefore false and remains an
explicit diagnostic. The accepted body is
`3d3762e28817a2bccf83986539c889d1e74e70139b2313affcc3d56cc1bb370b`.

The latest user report is "done". The normal listening confirmation comes from
the earlier paired-pass report; this correction does not invent a new listening
or display confirmation. Both channels are unclipped, with peaks0.13593/0.13248.
The separate hardware observation binds the original prediction, actual capture,
native result and exact export. The duplicate files and their original report
remain unchanged.

Current read-only export:
`experiments/exported-pattern1-FX16-corrected-clear-001/project.json`, with all31
file hashes and full native reconstruction verified. Global role and nibble order
remain unknown. The next [ordinary-playback control](pattern1-playback-global-control.md)
isolates this remaining global change. All45 affected checks pass; production
code remains unchanged since the full1,137-test run.
