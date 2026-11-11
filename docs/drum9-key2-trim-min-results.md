# Key2 supports a local endpoint interpretation

The capture passes all registered preservation checks and all **527 checksums** using
the normal crossing decoder at0.0063. Sound9 **key2 maps to selector9 / packet385**.
Its first field remains **4045**, owner remains0, and the second field changes
**8088→4172**, producing reference `cd0f00004c10000000`. Only bytes4/5 change; the
accepted key1 endpoint2000, other14 references, all backing codes, melodic sounds,
patterns and every unrelated native packet remain identical.

The exact registered **endpoint4172 (=4045+127)** prediction passes, along with the
first-field and broader lower-endpoint-range predictions. The mutually alternative
**literal length127** prediction fails and remains recorded. After saving, the user
reports **"done and confirmed I hear a click"** for key2. That supports a short local
endpoint window rather than treating4172 as the number of codes retained after the
start. It is a user-reported acoustic discriminator, not a measured duration. The127
difference at these two drum starts does not establish a universal minimum rule or
exact endpoint inclusivity.

- [Original predictions](../experiments/drum9-key2-trim-min-predictions-001.json)
- [Preservation and separate hypothesis results](../experiments/drum9-key2-trim-min-results-001.json)
- [Post-capture audition observation](../experiments/event-017-b-drum9-key2-trim-min/audition-observation.json)
- WAV SHA-256: `78f321ce42b7cfca70013487b70c62db4bd3dac57c27f7cb9f9a4c2de35692b6`
- Artifact SHA-256: `707528090cb1e487232b9b9af2a7d3ea8925632fd17edae0c69507f26f3970f3`
- Native body SHA-256: `09c5f71aad53947f1399cd3080a67a9c6f1ffb8a8fcc5df3dbd6102ac770450f`
- Stereo PCM16/44100Hz,1072960frames/24.330seconds; peaks0.16803/0.16086, no clipping indicators.

The bounded writer now supports **Sound9 keys1/2**, each at its own fixed start and
local endpoint interval: key1 start0/end127..4044, key2 start4045/end4172..8088. Both
controlled references may vary inside those separate guards; the remaining14 references
must match their literal original-copy values. This permits ordered plans editing both
controlled slices without forcing either neighbor back to its original endpoint. Other
keys, starts, drum slots and unknown backing layouts remain rejected.

For key2, the writer reproduces both complete genuine minimum/baseline bodies and the
inverse. The first generated candidate changes endpoint **4172→6045**, preserving
start4045 and selecting2000 codes under the explicit half-open preview convention.
Only two bytes in packet385 change; key1 remains2000. Software phase/count, native-body
and exact packet roundtrips pass, and the candidate inverse reproduces the whole source.
This new nonzero-start drum edit **still requires its own hardware test**.

The current export is **experiments/exported-drum9-key2-min-001/project.json**. Both
keyboard mappings are marked observed, but explicit project drum-preview opt-in still
exports **accepted key1 only**. The key2 candidate has a separate unpitched raw-code
preview at `slice-preview-48k.wav`,4096FLOAT mono frames/48kHz. Raw packet and source
files remain preserved; no speculative preview is added to the project in advance.

The full suite passes **405 tests in104.71seconds**, with lint/format checks passing for
123Python files. New tests preserve the failed length prediction, verify whole genuine
forward/inverse bodies, reject mixed endpoint bounds and types, keep broad and exact
hypotheses separate, reject wrong keyboard mapping, verify the exact nonzero preview,
compose two-slice plans and exercise CLI/candidate provenance and export scope.

See the [first key2 restore test](native-drum9-key2-end-restore-test.md),
[software validation](../experiments/generated-drum9-key2-end-001/software-validation.json)
and [hash-bound plan](../experiments/drum9-key2-end-plan-001/plan.json). The physical
control report retains its writer-disabled status at the time it was created; subsequent
software writer enablement is recorded separately in the experiment metadata.
