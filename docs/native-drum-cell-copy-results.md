# Generated drum-cell copy accepted

The recapture exactly matches the entire registered target with543 valid native
checksums. Normal sign-crossing decode at threshold0.0063 succeeds without recovery.
The user reports **"done and confirmed"** for restore, Sound10 Steps1/9, unchanged
Sound2 Step9 and Sound3 Steps1/5/9/13, and normal Pattern1 playback. These observations
are recorded separately from native-state validation; acoustic waveforms and arbitrary
polyphony have not been measured.

Only native packets5/7 change from the physical-note source. Pattern1 bytes411/412/413
and905 change from zero to13/248/131/16, copying Sound10's opaque **0df883/10** pair
from Step1 to Step9. The source drum note, both melodic notes on Step9 and all other
notes remain identical. All samples/references, other15 patterns, footer and every
other plain packet remain unchanged. No new packet, sample allocation or synthesized
key value is introduced.

- [Original registered target](../experiments/edited-drum-cell-copy-001/restore-registration.json)
- [Hardware validation](../experiments/edited-drum-cell-copy-001/hardware-validation.json)
- [User observations](../experiments/edited-drum-cell-copy-001/manual-observation.json)
- Capture: `experiments/edited-drum-cell-copy-001/capture.wav`
- Capture SHA-256: `5de811a38223d7b4f14dfc65ba1ff724ec4a36458c8413196dc71ab9d4d3d648`
- Artifact SHA-256: `0d6d518212530c82ad74d432de4693ff0ee7956bc349741aa18fff2552a532a5`
- Exact body SHA-256: `6f4e2cab0060a6ff1c63eaafe7b34ea7c4ee8e95fa5d2b88ee64d1c308e6c130`

The current export is **experiments/exported-verified-drum-cell-copy-001/project.json**.
It includes both Sound10/key1 events, the four melodic Sound3 key projections, Sound2's
Step9 event, every raw/source packet and the existing four melodic/three drum previews.
The project remains read-only. Compiler, software, export and original restore-registration
reports retain `hardware_verified: false`; this separate hardware report records the
accepted device result.

The copy/removal guards remain unchanged: only Pattern1/Sound10's observed key1 pair,
accepted nonzero copied sample context and calibrated Sound2/Sound3 neighbors are
supported. This exact generated three-sound Step9 copy is accepted. Unobserved keys,
other drum slots, note parameters and arbitrary polyphony remain outside the evidence.
The failed original melodicF0 auxiliary prediction remains preserved.

The next [physical key2 control](drum10-step9-key2-control.md) replaces only the Step9
drum note while retaining Step1/key1. It tests whether the auxiliary changes10 to11,
with a separate melodicF1 alternative and independent cell-preservation checks. No key2
writer or project key projection is enabled in advance, and this note control does not
establish Sound10/key2's sample-reference selector mapping.
