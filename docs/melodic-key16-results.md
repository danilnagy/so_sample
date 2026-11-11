# Keyboard endpoint results

The user completed the fixed-Step5 Sound3 key2-to-key16 control and supplied the capture.
All preservation/locality checks pass, and both independently registered hypotheses fit:
**only Pattern1 auxiliary byte834 changes F1→FF**. Primary `0df883`, samples, Steps1/9/13,
other patterns and every unrelated plain packet are unchanged.

All **511** checksums validate, with native frame end89396. The frame body SHA-256 is
`55311018711e4b4b798609ce7c40bedb613d6dbb246ea2423aea8b8049db9fe9`.
The source WAV SHA-256 is
`a0c0bea848c7c1bf56349e695edaae8740cd465d6df044512972d6c45ed5c0f1`.
See [registered results](../experiments/melodic-key16-results-001.json).

The initial sign-crossings decoder fails CRC at wire byte17902. Its artifact and
failure report remain preserved. The measured-clock decoder recovers the complete frame
using waveform signs, unique pre-frame alignment and all-quarter consistency checks,
without expected byte values or packet repair. This is a second independent recording
in which the already validated method resolves a crossing timing slip.
See [initial failure](../experiments/event-009-b-melodic-key16/initial-decode-failure.json)
and clock report (`experiments/event-009-b-melodic-key16/derived/analysis-002/clock-report.json`, a local research artifact, not in the repository).

The physical controls now support these Sound3 values:

| Keyboard key | Auxiliary byte | Low nibble |
| ---: | --- | ---: |
| 1 | F0 | 0 |
| 2 | F1 | 1 |
| 16 | FF | 15 |

The upper nibble remains opaque and unchanged. Keys3..15 have not been directly tested,
and no generated key16 restore has been tested. The independently registered **key7**
control now also passes, changing only FF→F6. The writer has expanded to the four
directly observed keys1/2/7/16, with other values still rejected; see
[middle-key control](melodic-key7-control.md). Endpoints alone are not presented as full
keyboard-range hardware verification.
