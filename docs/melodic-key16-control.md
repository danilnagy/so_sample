# Test the far keyboard endpoint

Completed: all control checks and both registered hypotheses pass. Only auxiliary
byte834 changes F1→FF, with primary0df883 and all unrelated data unchanged. The initial
crossing attempt is preserved; measured-clock decoding validates all511 packets.
See [endpoint results](melodic-key16-results.md). The original protocol below is retained.

The generated alternating-key pattern is now verified against its hardware recapture,
and the user explicitly confirms the alternating pitches. Keep this state as the next
baseline. We will replace **Sound3's note at Pattern1 Step5**, currently key2, with **key16**.

1. Keep playback stopped and write mode off. Select **Sound3** with sound+3, retaining
   Pattern1. Press **write**, tap **Step5 once** to remove its note, confirm the light
   goes off, then press **write** again to exit.
2. With write **off**, tap **key16** once to select/audition that melodic note. Press
   **write**, tap **Step5 once** to add it, then press **write** again to exit.
3. Reselect **Sound8**. Keep TONE, stopped playback and all other knobs, effects, tempo,
   pattern chain and recording settings unchanged. Record the complete stereo backup
   **before playing the changed pattern**, as
   **experiments/event-009-b-melodic-key16/capture.wav**.

Leave the replacement note in place. The other notes should remain: Step1 key1,
Step9 key1 and Step13 key2. Controls follow the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en).

The baseline WAV hash is
`c5add754a44ac012a44114156839349f64024c6a2f69660571dbb5b1d59c67ed`;
the verified body hash is
`91b37d61e3bc71de72748dfd846892e62a7d839a9332f13a6f9c56687cdeadf0`.
Its validated artifact is the measured-clock **analysis-002**, while the failed
crossing analysis-001 remains preserved and is not an eligible baseline frame.

Preservation checks require unchanged samples, other patterns and other note cells,
with511 valid packets and native frame end89396. Separately, we predict primary bytes
[198,201) stay `0df883`, and auxiliary byte834 changes **F1→FF**, representing index15.
That endpoint and the full4-bit key mapping are unverified hypotheses, not enabled
writer behavior. Control checks and hypothesis outcomes must remain separate.
See [registered predictions](../experiments/melodic-key16-predictions-001.json).
