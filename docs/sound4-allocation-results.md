# Second independent sample buffer observed

The fresh Sound4 recording passes all registered control checks and allocation
hypotheses. Normal sign-crossing decode at threshold0.0063 recovers679 checksum-valid
packets. Only selector3 gains data; every previous sound record, both drum-note keys,
all16 patterns and every other plain packet remain identical.

Sound4's new header is **00000000c06f000003**: first field0, second28608, owner3. Its
payload is32777 bytes, comprising the9-byte header and **32768 sample codes** in136
data packets. The original owner0 buffer remains65536 codes and unchanged byte for byte.
Packet count grows543 to679, native body by33457 bytes and frame end to123301. No
global allocator bookkeeping or relocation is observed in this recording.

- [Original predictions](../experiments/sound4-allocation-predictions-001.json)
- [Measured allocation](../experiments/sound4-allocation-results-001.json)
- [Independent sample analysis](../experiments/sound4-sample-analysis-001.json)
- Capture: `experiments/event-022-b-record-independent-sound4/capture.wav`
- Capture SHA-256: `06ba6534872d05e434485b031f458b1289d6acaa37dc59ac2482b3a8eb1c25a0`
- Artifact SHA-256: `f30c99ed814fea1223983d0c5279e74d272d42c2464ea958b69276f62b604312`
- Body SHA-256: `523f2dd9b29f1ffbfa94e453138aa72cc8a0ee8c75a6373c1d35b47b346fc803`

The existing codec/nominal-rate preview independently fits **1000.033Hz**, with99.98%
single-sine explained variance. Its thresholded active region is about0.39seconds;
manual record gating was never assumed to preserve the entire0.5second input exactly.
Frequency fitting searches the observed spectrum without restricting it to1000Hz.
This is extracted sample analysis, not a measured Sound4/key1 device playback recording.
The user reports "done"; a separate tone classification was not supplied.

Buffer capacity and stored endpoint are distinct. There are4160 code bytes beyond28608,
of which3974 are nonzero code bytes. They are preserved unchanged; they cannot simply
be treated as zero-byte padding. Their presence does not establish audible sound,
stale-memory content or allocator rules. The data-packet payload histogram is128 packets
of255bytes, one25-byte packet and seven16-byte packets.

The current export is **experiments/exported-second-owner-001/project.json**, with five
melodic previews including **samples/04.wav**, three existing drum previews, all patterns
and all raw/source bytes. Sound4 reads owner3 and exports58590FLOAT frames at48kHz
under the existing zero-start endpoint policy. The sample's complete32768-code buffer,
including the tail, remains in the raw native/source view. Export reports remain
software-only.

The observed32768 and earlier65536 allocations suggest candidate capacity rules, but
two manually gated examples cannot distinguish rounding, fixed pools or other policies.
No allocator/resizing writer is introduced. The next [Sound4-to5 physical copy](sound4-to5-copy-control.md)
establishes a retained reference before studying re-recording Sound4 at a different length.
That sequence can reveal whether shared data stays shared, moves ownership or is copied
when the original sound is overwritten.
