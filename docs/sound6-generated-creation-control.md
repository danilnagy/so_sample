# Restore the first generated sample into empty Sound6

The next backup is **experiments/edited-sound6-create-001/restore.wav**.
It populates currently empty melodic Sound6 with a self-owned32768-code buffer,
header `00000000c078000005` (start0/end30912/owner5). The generated500Hz tone fills
the30912-code window, about1.32seconds at the nominal rate. Its1856 tail codes are zero.
All existing sounds, every pattern and all other plain packets remain unchanged.

The source is the hardware-verified generated shrink recapture. The empty Sound6
selector already exists in that backup; no new selector or global settings are created.
The experimental helper copies the observed Sound4 small-buffer page geometry and
sets the new owner byte to selector5. It rejects an occupied destination, existing
references to the empty owner, unknown slot/code layouts, malformed full-buffer
ownership and unrelated source/template changes.

The helper is limited to Sound4 reconstruction and this Sound6 candidate. Applied to
the earlier physical empty-Sound4 recording with its independently captured codes,
it reproduces that entire native body exactly. For the new Sound6 target, removing
only the inserted data packets reproduces the complete pre-edit source body.
The synthesized WAV passes strict phase and full native-body/plain-packet roundtrip.
The tone independently fits500Hz. Its fit uses explicit60000-frame analysis-only
silence padding; the saved preview contains only the1.32second logical window.

Total backing capacity rises131072 to163840 code bytes, below a previously observed
172032-code state. This is a conservative bound on this test, not a hardware memory
limit or allocation-rounding rule. Creation in Sound6 remains hardware-unverified.

1. Restore the complete **restore.wav** above through the proven stereo receive
   path at the established playback level: **write + sound + record** to receive.
2. Select **Pattern1 / Sound8 / TONE**, playback stopped, write off. Keep both knobs
   and all other settings unchanged.
3. **Before audition or pattern playback**, save a complete stereo backup at the
   successful reduced recording levels as
   **experiments/edited-sound6-create-001/capture.wav**, including a second of trailing silence.
4. After saving, audition **Sound6/key1** for the new lower tone lasting about1.3seconds.
   **Sound4/key1** should retain its higher1.3second tone and **Sound5/key1** its old
   shorter tone. Check **Pattern1** still plays its previous alternating pitches/drums.
   Return to Sound8/TONE stopped/write off and report restore acceptance and checks.

The target has951 packets/end190215. Its immutable registration pins source, WAV,
artifact, entire native-body and Sound6 record hashes before hardware testing.
The recapture checker reports an empty/stale baseline as a failure and independently
checks all Sound6 codes, pattern preservation and every non-Sound6 packet.

- [Software validation](../experiments/edited-sound6-create-001/software-validation.json)
- [Restore registration](../experiments/edited-sound6-create-001/restore-registration.json)
- [Workflow audit](../experiments/generated-shrink-to-sound6-creation-workflow-validation-001.json)
- Preview only: `experiments/edited-sound6-create-001/sound6-preview.wav`
- Generator: `python -m scripts.make_sound6_creation_candidate --out-dir <fresh-directory>`
- After normal capture decoding: `python -m scripts.check_sound6_creation_restore`
- Restore WAV SHA-256: `6a59118e82b6db98b36fc67f4e72e7ec16ea65264cfc94412b1d8af4473540e6`
- Expected body SHA-256: `258bb81fdb8085ab24f7be4f841ed7ea577a69943ee34a4beccabffd5d9e44f6`

No public CLI/edit-plan allocator or arbitrary sample-slot creation is enabled.

Creation and audible checks are now confirmed, with the entire hardware recapture
matching the generated target. See [creation results](sound6-generated-creation-results.md).
The next test is a [generated copy into empty Sound7](sound6-to7-generated-copy-control.md).
