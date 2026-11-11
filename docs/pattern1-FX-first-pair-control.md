# Complementary first-pair effect order

The exact accepted mixed body supplies the source for two fixed research
restores. All nonfooter bytes, including global131=7, stay exact. Both restores
clear the other fourteen effect nibbles; their targets differ only in the first
footer byte.

| Version | Restore folder | First footer byte | Low nibble first prediction | High nibble first prediction |
| --- | --- | --- | --- | --- |
| A | `experiments/edited-pattern1-FX-F6-first-pair-001` | F6 | First step up, second none | First step none, second up |
| B | `experiments/edited-pattern1-FX-6F-first-pair-001` | 6F | First step none, second up | First step up, second none |

Do A then B. For **each** folder:

1. Restore its `restore.wav` with the established stereo settings. Keep write off
   and both knobs untouched.
2. Before playing, save the complete backup as `capture.wav` at the established
   reduced level, with one second of trailing silence.
3. Make a **separate ordinary pattern recording** as `playback.wav`. Start recording
   while stopped, leave about one second of silence, then press PLAY. Record12 to15
   seconds of Pattern1 and stop it. Do not trim the leading silence or first note.

Do not press FX, enable write or move knobs. Preserve audio settings across the
two recordings. Report any deviations or uncertainty. This control needs four
new WAVs in total: one backup and one playback recording for each restore.

Both native targets and generated waveforms pass exact full-body/packet and
strict-phase roundtrips. The frozen audio method searches400..3000Hz in a fixed
150..3500Hz band. It finds the first detectable tone using a low-threshold anchor,
then measures80..140ms after its onset at three fixed thresholds in both
channels. Short/quiet first regions, clipping, stereo disagreement and failed
fits make the comparison unusable. It does not switch to a later usable note.

All six first-tone frequency ratios A/B near2 support the low-nibble-first local
hypothesis; ratios near0.5 support high-nibble-first. The fixed relative margin
is1%. Equal or other ratios remain inconclusive. Native target equality alone
does not establish playback order. The first audible event must correspond in
both restored starts; fit quality cannot prove that association. This is a new
local first-pair control, not an all-pattern ordering guarantee.

The method was frozen before either new audio capture. Existing audio was used
only to exercise detection before registration; its recording start was not
controlled for this experiment and it is not one of the two comparison inputs.
Synthetic checks verify independently known first frequencies, both order models,
quiet/short first-note rejection and unusable evidence. No retuning is allowed
after new data; a failed prediction or unusable comparison remains retained.

- [Frozen registration and method hashes](../experiments/pattern1-generated-FX-first-pair-order-registration-001.json)
- [Fixed preparation](../scripts/prepare_generated_pattern1_fx_nibble_pair.py)
- [Native/audio checker](../scripts/check_generated_pattern1_fx_nibble_pair.py)
- [First-tone method](../scripts/pattern1_fx_nibble_audio.py)
- [Accepted section-order evidence](generated-pattern1-FX-mixed-results.md)

Decode both backups independently at threshold0.0063 into their respective
`derived/analysis-001` directories. Run native checks with
`python -m scripts.check_generated_pattern1_fx_nibble_pair --leg a` and `--leg b`,
then run `--audio`. The audio comparison requires both successful full native
targets bound to actual capture/artifact hashes. Outputs stay hardware-unverified
until separately bound to physical observations. General per-step editing
remains disabled. All100 affected checks pass; production is unchanged since
the full1,246-test run.
