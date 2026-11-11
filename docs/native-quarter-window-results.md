# Second start window verified on hardware

The user confirms the restore and both tone checks passed. The clean retry backup
matches the entire registered target, with **511 valid checksums** and an exact native
body re-encode. Sound3 stores **start11716, endpoint19716, owner0**; the reference is
`c42d0000044d000000`. Only endpoint bytes4/5 of packet375 differ from the physical
minimum control. All backing sample codes, other sound records, patterns and unrelated
packets are identical. The normal crossing decoder at0.0063 succeeds directly.

- [Hardware validation](../experiments/edited-quarter-window-001/hardware-validation.json)
- Retry WAV: `experiments/edited-quarter-window-001/capture-retry.wav`
- WAV SHA-256: `fa3c5f47983a46b1ce1a7f533eff7df94f6cdefed13efe7bafa6b5f190ff86cb`
- Artifact SHA-256: `80b41e0fc6db479df2e61bd40cfc4988f70a6a0ecfb39de6c68cc736cd3b3eb3`
- Native body SHA-256: `933eca1c290f4fcde0718ddf87e342c3f5b059bbb96d070f98fd6145c342699a`
- Stereo PCM16/44100Hz,1077231frames/24.427seconds, peaks0.16776/0.16064 and no clipping indicators.

The first recording failed both crossing and measured-clock decoding. Its artifact,
diagnostic reports and failure status remain unchanged. The user uploaded the retry
over `capture.wav`; we preserved a separate `capture-retry.wav`. The first failed WAV
is no longer available, and its hash cannot recover its audio. The old failure report
is historical evidence; this new hardware report records the successful retry separately.
The cause of the first recording's corruption remains unidentified.

The regular writer now supports two **discrete, observed Sound3 starts**, with separate
local endpoint intervals:

| Start | Endpoint interval | Evidence |
| --- | --- | --- |
| 31393 | 31504..65535 | Two physical endpoint controls and accepted8000-code window |
| 11716 | 11827..19716 | Second physical start/minimum and accepted8000-code window |

`set-sound-end` preserves the current start. `set-sound-window` requires explicit start
and endpoint and accepts only these two start positions. Interpolated starts, other
sound slots, ownership layouts and endpoints beyond each local interval are rejected.
These bounds do not establish a general111-code minimum rule or exact endpoint inclusivity.
Endpoint values inside each interval remain local experimental interpolation; every
possible combination has not been restored individually.

Moving the window between11716/19716 and31393/39393 reproduces both complete independent
hardware bodies exactly, including every opaque packet. The hash-bound replay plan at
`experiments/replay-two-start-window-001/plan.json` generates the accepted second-start
WAV **byte for byte**. Compiler reports remain software-only; replay is not a new device
operation. See [replay audit](../experiments/two-start-window-workflow-validation-001.json).

The current read-only export, `experiments/exported-two-start-window-001/project.json`,
contains all16 patterns and previews for Sounds1/2/3/8. Sound3 explicitly reads8000 codes
under the half-open preview convention. No source audio is normalized or resampled in
the stored native state. The preview itself is unpitched, mono48kHzFLOAT.

The complete suite passes **359 tests in59.23seconds**. Ruff lint and formatting checks
pass for112Python files. Tests cover both whole hardware bodies and inverses, rejected
interpolated starts and crossed endpoint bounds, exact preview slicing, checksum-valid
wrong-endpoint rejection and CLI/edit-plan provenance. The next physical control is
[copying Sound1 into drumSound9](drum9-copy-control.md).
