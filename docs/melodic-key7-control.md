# Check an independent middle key

Completed: every control invariant and both registered hypotheses pass. Only auxiliary
byte834 changes FF→F6, with primary0df883 and all unrelated packets preserved. The
normal crossing decoder validates this capture directly. See [middle-key results](melodic-key7-results.md).
The original physical control instructions below are retained for provenance.

Keep the current four-note Pattern1 state. Sound3's Step5 now uses keyboard key16;
Steps1/9 use key1 and Step13 uses key2. The current verified capture supplies the
baseline, so only one new recording is needed.

1. Stop playback, leave write mode off and select **Sound3**, retaining **Pattern1**.
   Press **write**, tap **Step5 once** to remove its note, confirm the light goes off,
   then press **write** again to exit.
2. With write **off**, tap **key7** once to select/audition that note. Press **write**,
   tap **Step5 once** to add it, then press **write** again to exit.
3. Reselect **Sound8**. Keep TONE, playback stopped and all other knobs, effects,
   tempo, pattern chain and recording settings unchanged. Save the full stereo backup
   **before playing the changed pattern**, as
   **experiments/event-010-b-melodic-key7/capture.wav**.

Leave the replacement note in place. Controls follow the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en).

The independent prediction is **auxiliary834 FF→F6**, with primary bytes[198,201)
remaining `0df883` and every other state byte unchanged. This tests keyboard index6
away from the already observed0/1/15 endpoints. Preservation checks and hypothesis
outcomes are evaluated separately. See
[registered predictions](../experiments/melodic-key7-predictions-001.json).

The baseline is event-009-b-melodic-key16, using its **analysis-002** measured-clock
artifact. Source WAV SHA-256:
`a0c0bea848c7c1bf56349e695edaae8740cd465d6df044512972d6c45ed5c0f1`.
Verified body SHA-256:
`55311018711e4b4b798609ce7c40bedb613d6dbb246ea2423aea8b8049db9fe9`.
The failed crossing artifact remains diagnostic and is not a valid baseline packet frame.
