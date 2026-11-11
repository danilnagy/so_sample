# First generated tempo restore

The restore file is **experiments/edited-tempo80-001/restore.wav**. It changes the current
120 BPM backup to 80 BPM by replacing only byte129 in the second `0x7d5c` payload.
Samples, patterns and all other plain bytes are preserved. The complete target body
equals the independently genuine 80 BPM capture from the prior preset control.

1. Restore the complete **restore.wav** using the proven stereo receive path and
   established playback level. Receive uses **write + sound + record**.
2. Return to **Pattern 1 / Sound 8 / TONE**, stopped and write off. Keep both knobs and
   other settings unchanged. **Read the displayed BPM without pressing BPM**; the
   expected value is **80**. Report the actual displayed number.
3. **Before playing or auditioning**, record a complete stereo backup at the established
   reduced recording levels with one second of trailing silence. Save it as
   **experiments/edited-tempo80-001/capture.wav**.
4. After saving, play Pattern1 and check that it retains the same phrase at the slower
   80 BPM tempo. Existing samples should sound unchanged. Stop playback, return to
   Sound8/TONE, and report receive acceptance, displayed BPM and the checks.

The registration pins the exact returned120 source, independent genuine80 artifact,
candidate artifact, software report and restore WAV before testing. Software checks
include complete genuine-target equality, all checksums, strict full-phase roundtrip
and complete native-body/packet equality after decoding the generated WAV. The checker
keeps native integrity, single-byte tempo association, exact target/genuine equality
and independent display confirmation separate. Correct bytes do not substitute for a
display reading, and correct tempo does not hide changed sample data.

This is a research-only edit of this exact known source. No public tempo writer is
enabled. Software reports remain `hardware_verified:false`; three physical preset
observations are not acceptance of a generated tempo edit. No arbitrary BPM range is
claimed.

- [Software validation](../experiments/edited-tempo80-001/software-validation.json)
- [Restore registration](../experiments/edited-tempo80-001/restore-registration.json)
- Expected geometry: 815 packets, frame end byte156758
- Expected native body SHA-256: `2a1a594b027dcd228f20e2b72961e995b27a3c8378643d74ad03a323ce3c17ce`
- Restore WAV SHA-256: `ac450d4f900a16c02325787c4926a3a27a07554278b68ff552cfd670ed8f0832`
- After normal capture decoding: `python -m scripts.check_tempo80_restore --observed-bpm ACTUAL_DISPLAY_VALUE`

## Completed

The user confirmed the restored80 display and checks, and the entire recapture matches
both target and independent genuine80 state. See [results](generated-tempo80-results.md).
The bounded [preset edit](tempo-preset-edits.md) is now available. The next
[fine-tempo100 control](fine-tempo100-control.md) checks a non-preset value physically,
with no new restore required.
