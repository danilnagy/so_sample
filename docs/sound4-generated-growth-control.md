# Restore the first generated Sound4 buffer growth

The generated backup is **experiments/edited-sound4-growth-001/restore.wav**.
It grows unshared Sound4 from32768 to73728 codes using the exact header and ordered
packet sizes observed in event024. A new1750Hz tone fills the72128-code window,
about3.08seconds at the nominal sample rate. The1600-code tail is intentionally zero.
Sound5, every other sound and all patterns remain unchanged.

The experimental script rejects shared owner3, different source/target headers,
different page ordering, unsupported code capacity/types and any unrelated packet
difference between the source and layout template. Substituting the original template
codes reconstructs the entire independently captured event024 native body exactly.
The synthesized backup additionally passes strict phase, full native-body and plain
packet comparisons after WAV encoding/decoding. The independent tone fit is1750Hz.
Its measurement uses an explicitly recorded60000-frame analysis-only silence pad
because the activity detector estimates a noise floor from quiet audio; the sample
and saved preview retain their original3.08second window.

1. Use the proven stereo restore path and established playback level. Enter receive
   with **write + sound + record**, then play the complete **restore.wav** above.
   This restores the controlled backup and replaces Sound4's shorter tone.
2. Once reception finishes, select **Pattern1 / Sound8 / TONE**, playback stopped
   and write off. Keep both knobs and all other settings unchanged.
3. **Before audition or pattern playback**, record the complete stereo backup as
   **experiments/edited-sound4-growth-001/capture.wav**, at the successful reduced
   recording levels, retaining a second of trailing silence.
4. After saving, select Sound4/TONE and tap keyboard key1: expect a noticeably higher
   tone lasting about three seconds. Sound5/key1 should retain its old short tone.
   Check Pattern1 still plays its previous alternating pitches and drum notes.
   Return to Sound8/TONE stopped/write off and report restore acceptance and checks.

The registration pins the exact generated WAV/artifact/native-body hashes before
device testing. The recapture checker compares the entire target body and all sample
codes, plus independent preservation and geometry checks; a stale baseline fails.
Hardware acceptance and audition outcomes must be recorded separately from the
immutable software-validation report, which remains `hardware_verified:false`.

- [Software validation](../experiments/edited-sound4-growth-001/software-validation.json)
- [Restore registration](../experiments/edited-sound4-growth-001/restore-registration.json)
- Preview only: `experiments/edited-sound4-growth-001/sound4-preview.wav`
- Generator: `python -m scripts.make_sound4_resize_candidate --out-dir <fresh-directory>`
- After normal capture decoding: `python -m scripts.check_sound4_growth_restore`
- Restore WAV SHA-256: `a4789107a64c78f623a3c34ea0d366dfdbd481e539c65404cd5950d8c987fe15`
- Expected body SHA-256: `5e6946b26c77ec47d4bea2f02809810754d32369512353abd027a3109b01b401`

This is one template-based growth probe. General capacity selection, new-slot creation,
deletion, memory limits and mutations of shared buffers still require evidence.

The hardware restore and auditions are now confirmed, and the complete recaptured
body matches exactly. See [growth results](sound4-generated-growth-results.md).
The next control is the [generated shrink](sound4-generated-shrink-control.md).
