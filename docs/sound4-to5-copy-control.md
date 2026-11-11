# Copy the second independent sample before testing overwrite

Completed: Sound5 receives an exact owner3 reference, with680 valid checksums and all
prior state intact. Three fixed acquisition profiles recover the identical complete body;
the original failed profile and uploaded filename remain preserved. See
[results](sound4-to5-copy-results.md) and the
[next longer re-recording](shared-sound4-rerecord-control.md). Original registration
and instructions follow unchanged.

Sound4 now owns the new32768-code1kHz buffer. Sound5 is empty in the verified backup.
Keep both samples, every pattern note, both knobs, effects, tempo and chain unchanged.

1. Keep **Pattern1**, playback stopped and **write off**. Select **Sound4 / TONE**
   using **sound + 4**, then release the buttons.
2. Hold **write + sound**, press **5**, then release to copy Sound4 into Sound5.
3. Select **Sound8 / TONE**, playback stopped and write off. **Before audition or
   pattern playback**, record a full stereo PCM16/44100Hz backup at the same successful
   reduced levels as **experiments/event-023-b-copy-sound4-to-sound5/capture.wav**.
   Let the dump finish and retain a second of trailing silence.

Leave both sounds present and report deviations. Whole-sound copying follows the
[official guide](https://teenage.engineering/guides/po-33/en). The next planned study
will re-record Sound4 at a different length while Sound5 retains this copy, exposing
how the device handles shared ownership during overwrite.

Preservation checks require the exact existing owner0 and owner3 buffers/headers,
all other sound/reference records, all16 patterns, selector order and every non-Sound5
plain packet to remain identical. Sound5's destination group must initially be empty
and become populated. The source's entire32768-code buffer, including bytes beyond
its28608 endpoint, is retained.

Separate alternative hypotheses predict Sound5 is a nine-byte owner3 reference equal
to **00000000c06f000003**, or a duplicate self-owned owner4 buffer with the same codes.
The reference prediction separately expects one new packet,14 native body bytes and
frame end123315 (680 packets). Unexpected values or duplicate buffers are reported
independently; no target bytes repair the decoder. A passing reference copy alone does
not establish what later overwrite or deletion will do, and no allocator writer is
enabled in advance.

- [Preregistered predictions](../experiments/sound4-to5-copy-predictions-001.json)
- [Experiment metadata](../experiments/event-023-b-copy-sound4-to-sound5/experiment.json)
- [Validated independent recording](sound4-allocation-results.md)
- Baseline WAV SHA-256: `06ba6534872d05e434485b031f458b1289d6acaa37dc59ac2482b3a8eb1c25a0`
- Baseline body SHA-256: `523f2dd9b29f1ffbfa94e453138aa72cc8a0ee8c75a6373c1d35b47b346fc803`
- Source Sound4 payload SHA-256: `6e2600053f9d90ae26dc764f5155d31422503bb26a13d7d44b860c700109aa84`
