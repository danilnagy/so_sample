# Test copying one sound cell into an occupied step

Completed: the user confirms the requested light and playback checks. The recapture
matches the complete generated frame with all 511 checksums valid and all unrelated
state preserved. See [cell-copy results](native-sound-cell-results.md). The original
preparation below is retained for provenance.

Restore **experiments/generated-sound2-cell-001/restore-sound2-step9.wav** using the
same stereo playback path and levels that worked previously. Enter receive with
**write + sound + record** and play the whole 44.1 kHz stereo PCM16 transfer,
approximately 23.1 seconds.

1. Report whether restore succeeds.
2. **Before playing or inspecting steps in write mode**, select **Sound 8 / TONE**,
   with write off and playback stopped. Save a full stereo backup with the existing
   recording settings as **experiments/edited-sound2-cell-001/capture.wav**.
3. After saving, select **Sound 2** and enter write. Confirm **only Steps 1 and 9**
   are lit. **Do not tap any step buttons** during the check. Exit write.
4. Select **Sound 3** and enter write. Confirm **Steps 1, 5, 9, 13** are lit.
   Inspect without tapping steps, then exit write.
5. Play **Pattern 1** for one or two loops and report whether it plays normally.
   Stop, leave write off and return to **Sound 8 / TONE** afterward.

| Step | Sound 2 | Sound 3 |
| ---: | --- | --- |
| 1 | Existing key 1, primary 0d2831 | Existing key 1 |
| 5 | Empty | Existing key 2 |
| 9 | Copied key 1, primary 0d2831 | Existing key 7 |
| 13 | Empty | Existing key 16 |

Only Sound 2's primary bytes 387/388/389 and auxiliary byte 897 are added. All
Sound 3 notes, the original Sound 2 note, samples and unrelated packets are
preserved. This copies Sound 2's actual parameters intact; the failed prediction
that they equal Sound 3's parameters remains separately recorded.

- [Software validation](../experiments/generated-sound2-cell-001/software-validation.json)
- WAV SHA-256: `fb3715a6951f9563a8778537433ccb30c015818494043d333728e6ad3251147e`
- Expected native body SHA-256: `4362aa66f6c18e7351b39016eb1b801dfa4a6ce0f4935861d4aaf45c8737668b`
- Exactly 511 packets, frame end 89396; only plain packets 5 and 7 change.

The physical baseline is preserved in **experiments/event-011-b-sound2-layer/capture.wav**.
The new hardware evidence is recorded separately in the completed results above. Controls follow the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en).
