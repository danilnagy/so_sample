# Test the four calibrated pitches

Completed: the user confirms the four pitches matched the manual key reference. The
recapture matches the entire generated native frame, with all 511 checksums valid and
all unrelated state preserved. See [four-key results](native-four-keys-results.md).
The original preparation and instructions below are retained for provenance.

Restore **experiments/generated-four-keys-001/restore-four-calibrated-keys.wav** with
the same stereo playback path and levels that worked previously. It is44.1kHz PCM16,
approximately23.1seconds. Enter receive mode with **write + sound + record** and play
the entire transfer.

1. Report whether restore succeeds.
2. **Before playing**, retain Pattern1, Sound8 selected, TONE, write off, stopped
   playback and the same recording settings. Save the full stereo backup as
   **experiments/edited-four-keys-001/capture.wav**.
3. After saving, select **Sound3** with write off and audition keyboard keys
   **1,2,7,16** in that order. Play **Pattern1** for one or two loops and report whether
   its four evenly spaced short tones match that pitch order. Stop playback afterward.

The stored sequence is:

| Step | Keyboard key |
| ---: | ---: |
| 1 | 1 |
| 5 | 2 |
| 9 | 7 |
| 13 | 16 |

Manual audition provides the pitch reference; no ascending or descending scale order is
assumed. Leave this four-note pattern in place afterward. If capture is instead recorded
after playback, report that timing. The prior physical key7 backup remains preserved in
**experiments/event-010-b-melodic-key7/capture.wav**.
Controls follow the [official PO-33 guide](https://teenage.engineering/guides/po-33/en).

Only three auxiliary bytes change, all in plain packet7. Samples, primary note fields,
upper auxiliary nibbles and every other pattern remain unchanged. These four keyboard
values are directly calibrated from separate physical captures; other keys remain
unsupported. Its restore/playback/recapture evidence is now recorded separately in
the completed result linked above.

- [Software validation](../experiments/generated-four-keys-001/software-validation.json)
- WAV SHA-256: `4536ddb4ed196c1d7afb451ccc6e06f787068d93a134c7c6caa21533eaa694e5`
- Expected native body SHA-256: `9b87309f572b188cd1e1a2651b1ca4feec5cfa8fb669068631042ca8f49465f0`
- Exactly511 packets, frame end89396. Full phase/count roundtrip and exact native target
  recovery from the generated WAV pass. Genuine forward/inverse endpoint and middle
  capture bodies are reproduced exactly by the expanded writer.

The full suite passes **244 tests in69.17s**, including genuine middle/endpoint forward
and inverse bodies, all four calibrated key edits at multiple step positions and
rejection of untested keys and source parameters. Ruff lint and formatting checks pass
for all89 Python files.

Reproduce the candidate in a fresh output directory:

```powershell
.\.venv\Scripts\python.exe scripts/make_four_key_candidate.py experiments/event-010-b-melodic-key7/derived/analysis-001/capture.symbols.npz --out-dir experiments/generated-four-keys-002
```
