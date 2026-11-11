# Restore octave-up while preserving global131

Physical FX7 recording previously stored uniform footer6 together with global131
changing to9. The clear and latest plain-playback state instead has footerF and
global131=7. The new restore changes only the eight Pattern1 footer bytes to66,
leaving that global byte and all other state exact.

This tests a preregistered hypothesis: uniform footer6 alone restores the
user-recognized octave-up effect while global131 stays7. It does not assign a role
to that global byte, establish nibble order, infer every effect code or enable a
public FX writer. The constructor accepts only the exact current clear body and
the fixed raw value6.

1. Restore
   `experiments/edited-pattern1-FX6-global7-up-001/restore.wav` with the established
   stereo playback settings. Leave both knobs untouched.
2. With playback stopped and write off, record a new complete backup as
   `experiments/edited-pattern1-FX6-global7-up-001/capture.wav` **before listening
   playback**. Use the established reduced recording level and one second of
   trailing silence.
3. With write off, briefly play Pattern1. Report whether the octave-up effect is
   audible, including uncertainty, then stop. No FX button, write pass, knob
   movement or separate playback recording is needed.

The generated target body is
`1147b3d4952aa4ade735b011047bcf22a469855bc3e1fff9c6f6cd4c462ca495`.
Its waveform uses the accepted44.1kHz stereo PCM16 encoder at amplitude0.5.
Strict symbol and complete native body/packet roundtrips pass. Only eight footer
bytes change, and global131 stays7. Physical acceptance is pending.

- [Frozen registration](../experiments/pattern1-generated-FX6-global7-up-registration-001.json)
- [Software validation](../experiments/edited-pattern1-FX6-global7-up-001/software-validation.json)
- [Fixed constructor](../scripts/prepare_generated_pattern1_fx_up.py)
- [Recapture checker](../scripts/check_generated_pattern1_fx_up.py)
- [Latest unchanged physical state](pattern1-plain-playback-results.md)

After independently decoding the physical capture at threshold0.0063, run
`python -m scripts.check_generated_pattern1_fx_up`. The immutable software result
requires every packet and the entire native body to equal the fixed target.
The old recorded-up body with global9 fails this target even though its footer
is6. Native reception and listening are separate checks; no audible result is
inferred from bytes. Any failed exact-target prediction remains retained.

All58 affected tests pass, including actual generated-waveform decoding, the
genuine global9 counterexample and rejection of other global, note and sample
changes. Production code is unchanged since the full1,137-test run.

## Completed

The physical recapture now matches the complete generated target and every
packet, preserving global131=7. The user confirms hearing the octave effect in
the requested up-test context. See [results](generated-pattern1-FX-up-results.md)
for the literal listening scope and evidence. The next
[generated down/clear pair](generated-pattern1-FX-return-control.md) tests footer7
andF without changing the global byte. The original validation and registration
remain immutable and hardware-unverified.
