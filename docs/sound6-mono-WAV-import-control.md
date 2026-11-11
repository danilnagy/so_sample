# Restore a mono 44.1 kHz WAV imported with the new command

The backup is **experiments/edited-sound6-mono-WAV-import-001/restore.wav**.
It was produced by the public `import-sample` command from a saved mono PCM16 WAV:
a 0.75-second linear pitch sweep from 300 to 1,800 Hz at 44,100 Hz, peak 0.20 and 10 ms fades.

The actual saved 33,075 PCM frames are resampled 625/1176 to 17,579 native frames and
mu-law encoded without normalization. Automatic allocation selects the verified
32,768-code size, with 15,189 zero tail codes and header `00000000ab44000005`
(start 0/end 17,579/owner 5). It replaces the shorter Sound6 sample, retaining all other
samples, every pattern and opaque settings. Sound7 remains empty.

1. Restore the complete **restore.wav** above through the proven stereo receive path
   at the established playback level: **write + sound + record** to receive.
2. Select **Pattern 1 / Sound 8 / TONE**, stopped/write off. Keep both knobs and all
   other settings unchanged.
3. **Before audition or pattern playback**, save a complete stereo backup at the
   successful reduced recording levels as
   **experiments/edited-sound6-mono-WAV-import-001/capture.wav**, including a second
   of trailing silence.
4. After saving, check **Sound 6/key 1** plays a rising pitch sweep for roughly 0.75 seconds.
   **Sound 7/key 1** should remain silent, and Sound 4/key 1, Sound 5/key 1 and Pattern1
   should sound unchanged. Return to Sound 8/TONE stopped/write off and report receive
   acceptance and all checks, including any difference.

The registration pins the exact source artifact, input PCM file, compiler report and
target before testing. Software checks preserve every sample code and non-Sound6
packet, with strict complete-body/phase WAV roundtrip. Core recapture checks require
a valid changed state with populated Sound6 and unchanged patterns/selectors; capacity,
endpoint, imported-code prefix, complete buffer, logical window and whole-target
equality are independent hypotheses. A metadata change with intact codes is not
reported as sample-code loss. This is the first hardware check of mono 44.1 kHz and this
longer endpoint through the public importer; software replay is not that manual test.

- [Import report](../experiments/edited-sound6-mono-WAV-import-001/import-report.json)
- [Restore registration](../experiments/edited-sound6-mono-WAV-import-001/restore-registration.json)
- [Ordinary input metadata](../experiments/calibration-mono-WAV-import-001/source.json)
- Preview only: `experiments/edited-sound6-mono-WAV-import-001/preview.wav`
- After normal capture decoding: `python -m scripts.check_mono_WAV_import_restore`
- Expected geometry: 951 packets/end 190,215
- Input WAV SHA-256: `c93ad0fb225611002db5fe74822602a8b66432394b3262af0a01fed9cdf79e4d`
- Restore WAV SHA-256: `263dafa068a5e773738f3c2cc11f86ef734d650eb56aa5c1b2bfe90873e50764`
- Target body SHA-256: `5b557a2586907b90705bed847b63e33745d0cef85bc27e06f80e6f0601f29b7c`

## Completed

This restore is now hardware verified with all codes, metadata and the complete native
body preserved. See [results](sound6-mono-WAV-import-results.md). The accepted artifact
is `derived/analysis-002/capture.symbols.npz` at threshold 0.0063; the initial CLI-default
decode in `analysis-001` is retained as a failed diagnostic. The next
[copy probe](imported-sound6-to7-copy-control.md) is prepared.
