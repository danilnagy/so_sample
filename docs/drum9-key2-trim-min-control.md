# Locate drum key2 and test a nonzero-start boundary

Completed: key2 changes selector9 alone, retaining start4045 and yielding second4172.
The exact endpoint prediction passes; literal length127 fails. The user reports a click.
See [key2 results](drum9-key2-trim-min-results.md) and the
[next restore test](native-drum9-key2-end-restore-test.md). Original instructions follow.

The current before-state is the accepted Sound9/key1 endpoint2000 backup. Sound9's
candidate second record, selector9, stores first**4045**, second**8088**, owner0.
The key2 mapping has not yet been directly controlled. One new backup will test it.

1. Keep **Pattern1**, playback stopped and **write off**. Select **Sound9**, then tap
   **keyboard key2 once** to select the last-triggered slice.
2. Select **TRIM / tri**. Leave **knobA untouched**; turn **only knobB slightly clockwise,
   then fully counterclockwise** to register its minimum.
3. Return to **TONE / Sound8**. Before further audition or pattern playback, record a
   complete stereo backup using the successful settings as
   **experiments/event-017-b-drum9-key2-trim-min/capture.wav**.
4. After saving, select **Sound9 / TONE**, tap **key2 once**, and report whether it is
   a **very short click/burst** or a **sustained tone**. Reselect **Sound8 / TONE** without
   moving knobs; leave playback stopped and write off.

The [official guide](https://teenage.engineering/guides/po-33/en) assigns drum trim to
the last-triggered slice and knobB to length. The initial key2 tap chooses the slice;
write off keeps the existing pattern intact. Keep the new trim in place after recording.

Checks require only one of the16 existing Sound9 references to change, preserving its
nine-byte size and owner0. Both fields may move, with changes reported explicitly.
The other15 records, including the hardware-accepted key1 endpoint2000, all samples,
melodic sounds, patterns and unrelated packets must remain identical.

Separate hypotheses predict key2 maps to selector9 and its first field stays4045.
Alternative exact second values are **127** if stored as length or **4172** if stored
as endpoint4045+127. The127 offset comes from the observed key1 minimum and is a
transfer hypothesis rather than a general rule. A broader endpoint-range prediction,
4045<second<8088, is evaluated separately if exact predictions fail. The post-capture
audition supplies a user-reported acoustic discriminator; it is not a measured duration.

- [Preregistered predictions](../experiments/drum9-key2-trim-min-predictions-001.json)
- Baseline WAV SHA-256: `0ddaf2dd97497f4046ccf69a346b03284e5701296a91686f6880a3cf88770c3e`
- Baseline body SHA-256: `4eca78dcdf5521941bb07c0d16e4cad71115512021670c203d87256ce142e667`
- Candidate key2 packet index385, reference `cd0f0000981f000000`.

No new restore is required. The writer still supports key1 only; this registration does
not enable nonzero-start drum editing, other keyboard mappings or general inclusivity/minimum rules.
