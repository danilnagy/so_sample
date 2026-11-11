# Octave-down is verified; clear recording is duplicated

The octave-down backup independently decodes at threshold0.0063 to815 valid
packets and end byte156758. Its footer is `7777777777777777`, passing the raw7
prediction. Global payload byte131 changes9 to1, within the registered low-four
scope. Every other state byte is exact. Body SHA-256:
`e3a3dfbb517181d48b7356726dbf34097171e775a34c1a1e73b2ac570915d096`.

The user reports: "done, and confirmed i heard octave lower first time, then
normal second time". Lower-octave listening supports the first capture. The normal
second pass is retained as reported, but its supplied WAV is byte-for-byte identical
to the first WAV, including the same SHA-256:
`2ab2ebcf08a1f130e274cd05700ef7d6020963e23fc8bd72dca0c5bbfc3c99d1`.
This is duplicate raw input, not merely equal decoded device state. It cannot
verify the clearing action or adjudicate the original clear prediction.

The combined software report remains immutable. Its second footer comparison is
false because the duplicate still contains raw7, and that result is explicitly
qualified by a separate input-identity observation. No hardware-clear observation
is created. Both original WAVs and their derived files remain unchanged. A fresh
folder binds the actual clear recording to the unchanged earlier footerFF and
baseline-return predictions; it does not claim to precede the already reported
physical clear action.

Backup peaks are approximately0.1300/0.1275 full scale without clipping; levels
remain suitable. Current genuine read-only export:
`experiments/exported-pattern1-FX8-recorded-001/project.json`, with all31 hashes
and complete native reconstruction checked. Raw previews do not render octave effects.

- [Original combined software report](../experiments/pattern1-FX8-clear-results-001.json)
- [Octave-down hardware observation](../experiments/event-066-b-pattern1-FX8-recorded/hardware-observation-001.json)
- [Exact user report](../experiments/event-066-b-pattern1-FX8-recorded/manual-observation.json)
- [Duplicate input identity](../experiments/pattern1-FX8-clear-input-identity-observation-001.json)
- [Corrected clear capture](pattern1-FX16-corrected-clear-control.md)

The global byte's meaning and nibble order remain unknown; no public FX writer is
enabled. All34 affected corrected-input/FX checks pass. Production code is unchanged
since the full1,137-test run. Software reports remain hardware-unverified and
physical observations separate.
