# Recorded Sound 3 TONE adjustment changes pattern cells

The user reported **“sound 3 became louded, recordings uploaded.”** This supplies an
independent louder observation, without a display number or measured gain.

Both captures independently decode at threshold 0.0063 to 815 checksum-valid packets
ending at byte 156758. Plain playback A exactly matches the preceding joint100/swing9
body `1dab085d95629db191991a089c9e4e67f56fc2a7dd571b1674fa8dbce144e551`.
Recorded TONE B changes exactly 32 primary bytes across all 16 Sound 3 cells in
Pattern 1. Its new body is
`e34fbe7f6238c230deeacd96139b26e5ca88bb5f300a7831da87a24e32afaef7`.

| Prior raw cell category | Steps | Primary before | Primary after |
| --- | --- | --- | --- |
| Populated Sound 3 cells | 1, 2, 5, 9, 13 | `0df883` | `cdff83` |
| Previously empty Sound 3 cells | 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16 | `000000` | `c00f00` |

Every auxiliary byte remains exact, including the previously calibrated key values.
Other sounds, Pattern 1's footer, the other 15 patterns, all sample headers/codes and
all global bytes are unchanged. Tempo/swing remain 100/9. The primary-only location
hypothesis registered before collection passes. The no-change alternative fails for
the recorded action, while remaining true for the earlier stopped live adjustment.

A **post-observation literal model** exactly reconstructs the new body from genuine A:
OR first primary byte with `0xc0`, replace second primary byte's low nibble with `0xf`,
and preserve every other bit. This model was found after the first lock capture; it is
not retrospectively presented as a preregistered bitfield prediction. The earlier
control did not predict uniform maximum cells, but that uniform endpoint is observed.

The two high bits remain opaque TONE-pass-associated bits. The low nibble is a volume
candidate, supported by intentionally moving only B and hearing a louder sound. TONE
may snapshot more than one parameter; no volume-specific semantic, enable-bit meaning,
numeric display range or gain scale is confirmed yet. Primary data in a formerly empty
cell is not labeled a newly triggered note.

Separate immutable manual/hardware observations bind original WAVs, decoded artifacts,
the raw comparison and export. Capture peaks are approximately 0.160/0.153 with no
clipping; established levels remain suitable. Compiler/research reports remain
hardware-unverified, and no volume writer is enabled.

- [Raw comparison](../experiments/sound3-tone-lock-probe-results-001.json)
- [Plain-playback hardware observation](../experiments/event-043-a-sound3-plain-playback/hardware-observation-001.json)
- [Recorded-TONE hardware observation](../experiments/event-044-b-sound3-tone-volume-lock-up/hardware-observation-001.json)
- Current genuine export (`experiments/exported-sound3-tone-lock-maximum-001/project.json`, a local research artifact, not in the repository)

All 31 export content hashes and complete native-body reconstruction pass. Raw pattern
cells retain the new bytes; sample previews do not render the pattern's gain changes.

The next [recorded minimum and maximum return](sound3-volume-lock-range-control.md)
preregisters a falsifiable low-nibble-zero minimum and exact independent full-body
return to this loud endpoint. All 14 affected tests pass, including the actual 32-byte
model, candidate-mask preservation and failure of alternative minimum values or
hidden high-bit/global changes. Public writers are unchanged.
