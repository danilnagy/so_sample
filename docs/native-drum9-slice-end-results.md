# First generated drum-slice edit verified

The user reports **"done and pass"** for restore and both tone checks. The new backup
matches the entire registered target with **527 valid checksums** and exact native
re-encoding. Sound9/key1 retains start0/owner0 and stores endpoint**2000**, reference
`00000000d007000000`. Only bytes4/5 of packet383 differ from the genuine minimum
source. The other15 drum references, all backing codes, melodic sounds, patterns and
unrelated packets are identical. Normal crossing decode at0.0063 succeeds directly.

- [Hardware validation](../experiments/edited-drum9-slice-end-001/hardware-validation.json)
- WAV SHA-256: `0ddaf2dd97497f4046ccf69a346b03284e5701296a91686f6880a3cf88770c3e`
- Artifact SHA-256: `cfb6a1470674c6d8e9f42ec127c84f0605b7084c17e03ad06791acaa37cc52d3`
- Native body SHA-256: `4eca78dcdf5521941bb07c0d16e4cad71115512021670c203d87256ce142e667`
- Stereo PCM16/44100Hz,1099917frames/24.941seconds, peaks0.16809/0.16089 and no clipping indicators.

The user confirms a clear short Sound9/key1 tone and the unchanged longer Sound8/key1
tone. Exact hardware duration, pitch, gain and endpoint inclusivity were not independently
measured. This validates the registered local endpoint edit; it does not establish
arbitrary drum starts, other keys, sound slots or universal minimum rules. The original
exact79 minimum prediction remains failed. Compiler and candidate software reports
stay unchanged with `hardware_verified: false`; acceptance is recorded separately here.

Project export can now explicitly include the first calibrated drum slice with
**--calibrated-drum-slices**. This option is separate from `--calibrated-windows`, which
controls the nonzero-start Sound3 preview. Only Sound9/key1 in the local writer context
is supported. Unknown contexts stay raw with a reason instead of producing speculative
audio. Other fifteen slice previews and other drum slots remain unsupported.

The current export is **experiments/exported-verified-drum9-slice-001/project.json**:
all16 patterns, four melodic previews and **samples/09-slice-01.wav**. The drum preview
reads codes[0:2000] under the explicit half-open policy and contains4096FLOAT mono
frames at48kHz. It applies no keyboard pitch or gain changes. `preview_drum_slices`
records its sound/slice/file mapping separately from melodic `preview_sound_slots`.
All27 content hashes and the complete raw packet representation have been checked.

The full suite passes **393 tests in60.21seconds**, with lint/format checks passing for
120Python files. New tests verify the genuine complete target, reject checksum-valid
wrong endpoints and altered neighbors, check the exact unscaled preview, require separate
opt-in, preserve unknown contexts raw and retain every source/native packet unchanged.

The next [key2 minimum control](drum9-key2-trim-min-control.md) tests the adjacent
nonzero-start record while preserving the accepted first-slice edit.
