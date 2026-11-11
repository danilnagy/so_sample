# Sound5 shares the second independent owner

The physical Sound4-to5 copy passes every preservation check with680 valid native
checksums. Sound5 adds one nine-byte reference **00000000c06f000003**, exactly Sound4's
header: start0/end28608/owner3. The duplicated self-owned-buffer hypothesis fails.
Packet count grows679 to680, native body14 bytes and frame end123315. Both existing
sample buffers, all other records/patterns and every non-destination packet remain intact.

- [Original predictions](../experiments/sound4-to5-copy-predictions-001.json)
- [Measured results](../experiments/sound4-to5-copy-results-001.json)
- [Capture verification history](../experiments/event-023-b-copy-sound4-to-sound5/capture-verification-status-001.json)
- Uploaded recording: `experiments/event-023-b-copy-sound4-to-sound5/po_33_61.wav`
- Byte-identical analysis alias: `capture.wav` in the same folder
- Capture SHA-256: `9cf4096737c90537a7dacbb0d4f4436c8730958468a7313eee97e73d5ed0c387`
- Selected artifact SHA-256: `6df29f28c9cd7d5830e4f3c449932eeb89e2268613cf50279bc9b14e6cb3cab2`
- Body SHA-256: `eb19589f3bf193f81611a7322bf79c98881531f24269eed2b8c67e342d731dfb`

The original0.0063 crossing profile fails the first packet checksum. Measured-clock
recovery using that acquisition also fails at the first packet; no clock artifact is
accepted. Three fixed profiles, chosen before their outcomes—0.004/0.01/0.02—each recover
all680 checksums and the same complete native body. Analysis003 at0.004 is selected as
the first valid profile in that order. Expected copy values never guide acquisition,
alignment or symbol repair. The default decoder, original WAV, failed crossing artifact
and all diagnostic reports remain unchanged. This indicates acquisition/threshold
sensitivity; its exact cause and a general threshold policy are not established.

The current export is **experiments/exported-second-owner-copy-001/project.json**,
with six melodic previews, three drum previews, all patterns and all raw/source data.
`samples/04.wav` and `samples/05.wav` are byte-identical, using the same owner3 window.
The full32768-code buffer and its tail are retained once in the raw native data.
Export reports remain software-only. The original uploaded filename and its content
are retained; the canonical alias is separately documented in `capture-import.json`.

This extends shared-reference evidence to a second independent owner. It does not
establish overwrite/deletion behavior or a general allocator. The next
[longer re-recording control](shared-sound4-rerecord-control.md) replaces Sound4 with a
distinct two-second tone while retaining Sound5, independently testing whether the old
buffer is transferred to the copy, the copy follows the new sound, or another policy
applies. No allocator/resizing writer is introduced.
