# Restore a generated Sound6-to7 shared reference

The next backup is **experiments/edited-sound6-to7-copy-001/restore.wav**.
It copies the new Sound6 sample into currently empty Sound7 by inserting the exact
nine-byte reference `00000000c078000005` under selector6. Sound6 retains its entire
32768-code buffer under owner5. Both sounds resolve to the same30912-code500Hz window,
about1.32seconds at the nominal rate. No backing buffer is duplicated.

Every existing sound, all patterns and all non-Sound7 plain packets remain unchanged.
The total backing capacity stays163840 codes. Only one data packet and14 encoded-body
bytes are added:952 packets/end190229. Sound7's existing selector/global settings are
preserved, and no parameters or pattern notes are changed.

The research helper supports only the previously observed Sound4-to5 reconstruction
and this Sound6-to7 candidate. It rejects unsupported pairs, an occupied destination,
wrong source headers/capacities, existing source sharing and references to the empty
destination. The same helper reconstructs the earlier physical Sound4-to5 copy's
entire native body exactly. The new candidate passes strict phase and full packet/body
WAV roundtrip checks; both decoded previews are identical. Removing just the inserted
reference reproduces the pre-edit source body exactly.

1. Restore the complete **restore.wav** above through the proven stereo receive path
   at the established playback level: **write + sound + record** to receive.
2. Select **Pattern1 / Sound8 / TONE**, playback stopped, write off. Keep both knobs
   and all other settings unchanged.
3. **Before audition or pattern playback**, save a complete stereo backup at the
   successful reduced recording levels as
   **experiments/edited-sound6-to7-copy-001/capture.wav**, including a second of trailing silence.
4. After saving, compare **Sound6/key1** and **Sound7/key1**: expect the same lower tone
   and duration, about1.3seconds. **Sound4/key1**, **Sound5/key1** and **Pattern1** should
   sound unchanged. Return to Sound8/TONE stopped/write off, retaining both sounds,
   and report restore acceptance and all checks.

The immutable registration pins every file/body hash before the device test. The
recapture checker requires the exact nine-byte reference, preserved full Sound6
buffer and owner5 referrers `[5,6]`, plus entire-target and all unrelated-state equality.
Audition outcomes are recorded separately from software evidence.

This prepares a known shared-owner state for a subsequent physical deletion control.
Deletion behavior remains unverified; no deletion operation is performed in this test.

- [Software validation](../experiments/edited-sound6-to7-copy-001/software-validation.json)
- [Restore registration](../experiments/edited-sound6-to7-copy-001/restore-registration.json)
- [Workflow audit](../experiments/sound6-creation-to-reference-copy-workflow-validation-001.json)
- Preview only: `experiments/edited-sound6-to7-copy-001/sound7-preview.wav`
- Generator: `python -m scripts.make_sound6_to7_copy_candidate --out-dir <fresh-directory>`
- After normal capture decoding: `python -m scripts.check_sound6_to7_copy_restore`
- Restore WAV SHA-256: `63591a69d9a32b24e675b6af7fc2276b6fd572eff8c6c7ae79b61f0ef574a315`
- Expected body SHA-256: `c90ffd7eb2a11d83ab0492ba6b4920d6b0c77342b6c09eb35e9b28a1f7b14a00`

Hardware copy acceptance is pending; public CLI/edit-plan scope is unchanged.

The generated copy and audible checks are now confirmed, with an exact whole-body
hardware recapture. See [copy results](sound6-to7-generated-copy-results.md). The next
control is [physical deletion of shared Sound6](shared-sound6-deletion-control.md).
