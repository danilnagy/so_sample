# Replace only the layered Step9 drum note with key2

Completed: all preservation checks pass with543 valid checksums. Only auxiliary905
changes10 to11, primary0df883 is retained and the alternative melodicF1 prediction
fails. See [results](drum10-step9-key2-results.md) and the
[next independent sample recording](sound4-allocation-control.md). Original predictions
and instructions follow unchanged.

Use the current accepted drum-cell-copy state. Pattern1/Sound10 has key1 notes at
Steps1 and9; Sound2 remains at Step9 and Sound3 at Steps1/5/9/13. Both drum notes
store the observed opaque0df883/10 pair. Keep the source Step1/key1 and every melodic
note intact. Keep both knobs, effects, tempo and chain unchanged.

1. Retain **Pattern1**, playback stopped and **write off**. Select **Sound10 / TONE**.
2. Press **write**, tap the lit **Step9 once** to remove only its Sound10 note, then
   press **write** again to exit. Keep Step1 lit. If Step9 is unexpectedly unlit, exit
   without toggling and report the deviation.
3. With **write off**, tap **keyboard key2 once** to select that drum slice. Press
   **write**, tap **Step9 once** to add the key2 note, then press **write** to exit.
4. Select **Sound8 / TONE**, playback stopped and write off. **Before playing the
   pattern**, save a full stereo PCM16/44100Hz backup at the successful reduced recording
   levels as **experiments/event-021-b-drum10-step9-key2/capture.wav**. Let the entire dump
   finish and retain a second of silence before stopping the recording.

Leave Step1/key1 and Step9/key2 present and report deviations. Key selection happens
outside write mode; step toggling happens inside write mode, following the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en).

Preservation allows changes only to Sound10's Step9 primary[411:414] and auxiliary905.
The source Step1/key1, every other pattern byte, all melodic notes, every sample/reference,
other15 patterns, footer and every other plain packet must remain identical. Exactly543
packets/frame end89844 are required. The target note must remain populated, but its raw
primary and auxiliary values are not forced to the predictions.

Separate hypotheses predict unchanged primary0df883, auxiliary**11** (17 decimal)
versus melodic**F1** (241 decimal), exactly one changed pattern byte905 from16 to17,
and only native packet7 changed. Both exact auxiliary alternatives may fail; every raw
value and each hypothesis fit is reported independently. A different primary or another
allowed byte change remains a hypothesis failure even if preservation passes.

This tests the recorded key2 note action. It does not independently map keyboard key2
to Sound10 sample selector25: that mapping still needs a reference-level control. No
key2 writer, key setter, key2 projection or general auxiliary nibble interpretation is
enabled before the control is evaluated. Existing key1 copy/removal support remains
bounded to its observed pair and sample context.

- [Preregistered predictions](../experiments/drum10-step9-key2-predictions-001.json)
- [Experiment metadata](../experiments/event-021-b-drum10-step9-key2/experiment.json)
- [Accepted baseline](native-drum-cell-copy-results.md)
- Baseline WAV SHA-256: `5de811a38223d7b4f14dfc65ba1ff724ec4a36458c8413196dc71ab9d4d3d648`
- Baseline artifact SHA-256: `0d6d518212530c82ad74d432de4693ff0ee7956bc349741aa18fff2552a532a5`
- Baseline body SHA-256: `6f4e2cab0060a6ff1c63eaafe7b34ea7c4ee8e95fa5d2b88ee64d1c308e6c130`

If ordinary decoding fails, retain that attempt. Any established measured-clock recovery
must use waveform/pre-frame evidence without expected note bytes, a target frame or
checksum-guided repairs.
