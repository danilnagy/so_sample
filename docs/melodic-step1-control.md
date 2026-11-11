# One melodic note in the verified minimal state

Completed: the new capture passes every registered preservation and locality check.
Only Pattern1 bytes6/7/8 and770 change; all samples and Patterns2..16 are unchanged.
All511 checksums validate. See [melodic results](melodic-step1-results.md).
The original control instructions below are retained for provenance.

The latest sample-replacement recapture is validated and Pattern1 is empty. Keep this
state; no new restore, reset, sample recording or empty baseline is needed.
The target is **Pattern1, Step1, Sound3, melodic keyboard key1**. Sound3 retains the
brief750Hz source tone and its counter8000.

1. Keep playback stopped and write mode off. Select **Sound3** with sound+3, then tap
   **key1** once to select/audition the note.
2. Press **write** to enter grid editing. Tap **Step1 once** to add the note, then press
   **write** again to exit. Only Step1 should be lit for this selected sound.
3. Reselect **Sound8** using sound+8. Keep TONE, stopped playback and the same knobs,
   effects, tempo, pattern chain and recording settings. Record a complete stereo backup
   as **experiments/event-007-b-melodic/capture.wav**.

Do not play the pattern before this backup. Leave the added note in place afterward.
If Step1 is unexpectedly already lit before adding the note, or a different action is
needed, report that rather than toggling an uncertain event. This is a controlled edit
to the currently empty pattern; the prior verified backup is preserved.

Selection, write-mode grid editing and backup controls follow sections4/5/8 of the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en), checked2026-10-08.
The guide distinguishes melodic keys from drum slices; key1 here is a melodic keyboard
key, not a slice number. No precise note bitfield is assumed from the button label.

The registered baseline is edited-sample-001, source SHA-256
`94b9b95f3468f4781d52542756cb858479a2a4cd3969826ad31658479919312d`.
All sample data and Patterns2..16 should remain unchanged. Pattern1's new primary data
should lie in Step1 span[0,48); auxiliary changes should lie in[768,784), with the
opaque footer unchanged. The expected packet count is511 and native frame end89396.
These are checks to evaluate, not established results.
See [registered predictions](../experiments/melodic-step1-predictions-001.json).
