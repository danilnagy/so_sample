# Set minimum length at the fixed nonzero start

Completed: all preservation checks pass, start31393 stays fixed, and second31504
rejects both exact registered values79/31472. A subsequent user-reported minimum burst
supports a broader local endpoint interpretation. See [minimum results](sound3-start-min-results.md).
The original protocol and hypotheses below are retained for provenance.

Use the current Sound 3 start-control state. Its first raw field is 31393, second
field 65535, and owner 0. The current backup supplies the baseline; only one new
recording is required.

1. Keep **Pattern 1**, playback stopped and write off. Select **Sound 3**.
2. Press **FX** until **TRIM / tri**. Turn **only knob B fully counterclockwise**
   to set minimum length. **Leave knob A untouched**.
3. Return FX to **TONE**, select **Sound 8**, and retain write off, stopped playback
   and all other settings. Record the full stereo backup **before audition or pattern
   playback** as **experiments/event-013-b-sound3-start-min/capture.wav**.

Leave the changed setting in place afterward. No additional playback check is required
for this control. The [official guide](https://teenage.engineering/guides/po-33/en)
assigns knob B to length in TRIM mode.

The registered preservation checks require start 31393, owner 0, all backing codes,
other sound records and every pattern cell to remain unchanged. Changes are allowed
only in bytes 4..7 of the existing Sound 3 reference, with unchanged packet count and
lengths. A change in the first field would fail this fixed-start control assumption.

The independent zero-start minimum recording has header **000000004f00000000**
and second field **79**. Separate preregistered predictions for this nonzero-start
control are:

| Alternative | Expected second field |
| --- | ---: |
| Stored length | 79 |
| Stored endpoint with the same minimum raw width | 31472 (=31393+79) |

These alternatives are evaluated independently of preservation. Other results are
retained as hypothesis failures. A stored width alone does not determine inclusive
versus exclusive endpoints, and 65535's earlier meaning remains unresolved.
No nonzero-start writer or extractor is enabled yet.

- [Preregistration](../experiments/sound3-start-min-predictions-001.json)
- Baseline WAV SHA-256: `24502f734e1d9170a1c5a4ac89d104fafeec3514478f39749919521336f68673`
- Baseline body SHA-256: `4b697a34bea74f34654107463a9586afe31e9db1b55bf11f4f057f6e7f72ddc2`
- Zero-start minimum capture SHA-256: `09d7f911938ac6c4c21264db92c894db40895b2b18ea6ca324c345ac7eac7d70`

Measured-clock decoding, if needed, must not use these expected fields or repair packets.
