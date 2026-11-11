# First native trim edit: hardware validated

The user reports successful restore and both requested tone checks. The supplied
post-test backup matches the generated encoded body exactly, with all **511** packet
checksums valid. Sound3 has counter8000; Sounds1/2/8 retain64704, and the entire backing
sample buffer is unchanged. See [hardware validation](../experiments/edited-trim-001/hardware-validation.json).
The independent amplitude-clock check finds no interior quarter-sign disagreements.
The separately generated unedited control has not been tested on hardware.

The original test instructions and expectations below are retained as the protocol.

Restore **experiments/generated-sound3-short-001/restore-sound3-short.wav** using the same
stereo playback path and levels that worked for earlier restore tests. It is44.1kHz PCM16,
about23.1 seconds, with the same corrected waveform model. All software checks pass;
the following procedure was used for its hardware validation.

1. Connect computer stereo output to PO-33 line input. Enter receive mode with
   **write + sound + record**, then play the entire generated WAV once.
2. Report whether restore completes successfully. With write off and the sequencer
   stopped, select **Sound3** and tap **key1** once. It should play a brief tone of
   roughly0.23s rather than the previous1.25s audible tone.
3. Select **Sound8** and tap **key1** once. It should retain the original longer tone.
   Sounds1/2/8 have unchanged reference counters and share unchanged sample data.
4. Reselect **Sound8**, retain TONE, empty Pattern1, write off, playback stopped and
   unchanged settings. Record a full stereo backup as
   **experiments/edited-trim-001/capture.wav**.

The [official restore guide](https://teenage.engineering/guides/po-33/en) specifies this
receive-mode combination and notes that restore replaces samples and patterns. The
original untrimmed backup remains **experiments/empty-001-h-sound3-copy-return/capture.wav**.
This candidate was built from that saved state.

The expected edited encoded body SHA-256 is
`0191ad7ee47710d5bcb117d8b3d1c9774c972ff06df829f9cb302d2f2046c4d7`.
After re-capture, checksum parsing must show Sound3 counter8000, counters64704 for1/2/8,
unchanged backing samples and the expected packet body. Raw capture carrier counts remain
separate from this protocol-domain comparison.

If the edited file fails, report the behavior and stop changing settings. An unedited
control is already prepared at **experiments/generated-sound3-short-001/control-restore.wav**
for a separate diagnostic; its software packet body matches the original. Hardware
acceptance of either generated file is not assumed.
