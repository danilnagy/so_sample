# Generated Sound6-to7 sharing restores exactly

The user confirmed restoration, matching Sound6/Sound7 key1 tones and unchanged
Sound4/Sound5/Pattern1 checks. The hardware recapture passes all952 native checksums
with the normal0.0063 acquisition. Its complete native body and every plain packet
match the generated copy target exactly.

Sound7, selector6, has the exact nine-byte reference `00000000c078000005`
(start0/end30912/owner5). Sound6 still owns the complete original32768-code buffer,
unchanged header and every code. Owner5's only referrers are selectors5/6: Sound6 and7.
All prior sounds, all16 patterns and every non-Sound7 plain packet remain identical
to the pre-copy baseline. No buffer is duplicated; capacity stays163840 codes.

The user confirms the same lower tone and duration in both sounds. Their exported
preview WAVs are also byte-identical. This verifies this generated reference copy,
alongside earlier physical sharing under owners0/3. It does not establish deletion,
shared-buffer mutation, arbitrary copying or per-slot parameter copying.

- [Exact native comparison](../experiments/edited-sound6-to7-copy-001/hardware-recapture-results-001.json)
- [Separate hardware acceptance](../experiments/edited-sound6-to7-copy-001/hardware-acceptance-001.json)
- [User observation](../experiments/edited-sound6-to7-copy-001/manual-observation.json)
- [Original registration](../experiments/edited-sound6-to7-copy-001/restore-registration.json)
- Current read-only export: `experiments/exported-generated-sound6-to7-copy-001/project.json`
- Capture SHA-256: `9737239d8d7b8f221eb23b0d7b8240f0a8799c3ad48482dc9e16ab94f4fc313f`
- Artifact SHA-256: `86f4d0e0b23b03494edb622e8de25e9b756b48f558d9f89943b03d0529184def`
- Native body SHA-256: `c90ffd7eb2a11d83ab0492ba6b4920d6b0c77342b6c09eb35e9b28a1f7b14a00`

All33 export content hashes pass, with eight melodic/three calibrated drum previews
and exact source/raw records. Software reports remain `hardware_verified:false`;
the immutable acceptance report records the completed manual test separately.
The next [physical shared-owner deletion](shared-sound6-deletion-control.md) deletes
only Sound6 while retaining Sound7, exposing how the device serializes surviving data.
