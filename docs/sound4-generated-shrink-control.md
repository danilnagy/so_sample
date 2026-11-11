# Restore the generated Sound4 shrink

The next backup is **experiments/edited-sound4-shrink-001/restore.wav**.
It shrinks unshared Sound4 from73728 to32768 code bytes using the exact smaller
header and page packet geometry from the physical event025 capture. A new2250Hz tone
fills the30912-code window, about1.32seconds at the nominal rate. Its1856 tail codes
are intentionally zero. Sound5 and all other sounds/patterns remain unchanged.

The research helper now accepts either direction between the two exact observed
layouts, rejecting shared owners, equal capacities, unknown headers/page ordering,
wrong code counts/types and unrelated template/source differences. Applying the
inverse with the original smaller capture's codes reconstructs its complete native
body exactly. The generated shrink passes strict phase and full packet/body WAV
roundtrip checks. Its independent tone fit is2250Hz, using the same explicit60000-frame
analysis-only silence pad as the full-window growth tone. The saved preview itself
contains only the1.32second window.

1. Use the proven stereo restore path and playback level. Enter receive with
   **write + sound + record**, then play the complete **restore.wav** above.
2. Select **Pattern1 / Sound8 / TONE**, playback stopped, write off. Keep both knobs
   and all other settings unchanged.
3. **Before audition or pattern playback**, save a complete stereo backup at the
   successful reduced recording levels as
   **experiments/edited-sound4-shrink-001/capture.wav**, with a second of trailing silence.
4. After saving, audition **Sound4/key1**: expect a higher tone lasting about1.3seconds,
   shorter than the previous3second tone. **Sound5/key1** should retain the old short
   tone, and **Pattern1** should play its previous alternating pitches/drum notes.
   Return to Sound8/TONE stopped/write off and report restore acceptance and all checks.

The registered target has815 packets/end156758 and pins every generated file/body
hash before the device test. The checker rejects a stale grown backup and compares
the entire target, all Sound4 codes and independent preservation checks.

- [Software validation](../experiments/edited-sound4-shrink-001/software-validation.json)
- [Restore registration](../experiments/edited-sound4-shrink-001/restore-registration.json)
- [Workflow audit](../experiments/generated-sound4-growth-to-shrink-workflow-validation-001.json)
- Preview only: `experiments/edited-sound4-shrink-001/sound4-preview.wav`
- Generator: `python -m scripts.make_sound4_resize_candidate --direction shrink --out-dir <fresh-directory>`
- After normal capture decoding: `python -m scripts.check_sound4_shrink_restore`
- Restore WAV SHA-256: `9fb25b37196de46a708a67b087fce34b931cba9f3067e86862b3cc9eab656fbb`
- Expected body SHA-256: `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0`

Hardware shrink acceptance is pending. Public CLI/edit-plan allocation operations
remain unavailable until supported within an appropriate validated scope.

The shrink restore and auditions are now confirmed, and the entire recaptured body
matches exactly. See [shrink results](sound4-generated-shrink-results.md). The next
control is [generated sample creation in empty Sound6](sound6-generated-creation-control.md).
