# Joint tempo 100 and swing 9 restore

The existing public plan compiles two sequential edits from the verified current
137 BPM/swing-6 capture:

```json
[
  {"operation": "set_tempo", "bpm": 100},
  {"operation": "set_swing", "value": 9}
]
```

Only second `0x7d5c` payload bytes 129 and 130 change. All samples, patterns, other
global bytes and sound parameters remain exact. Tempo and swing edit order produces
the same packets in software. The compiled WAV passes strict phase round trip and
complete target body/packet recovery; this new combination is hardware-unverified.

Target body SHA-256:
`1dab085d95629db191991a089c9e4e67f56fc2a7dd571b1674fa8dbce144e551`.
Restore WAV SHA-256:
`46ec1c35a8f080547eb2a38a81f8b83524ec18452dac9606a699b1340e8a9d3f`.

1. Restore the entire `experiments/edited-joint-tempo100-swing9-001/restore.wav` using
   the established stereo path and playback level.
2. Keep both knobs untouched. Select Pattern 1 / Sound 8 / TONE, stopped and write off.
3. Read the ordinary BPM display without pressing BPM or moving knobs. Report the
   actual reading; the expected value is **100**. Do not turn A to read swing.
4. Before playing the pattern, record a complete stereo backup as
   `experiments/edited-joint-tempo100-swing9-001/capture.wav` with the established reduced
   levels and one second trailing silence.
5. After saving, briefly play Pattern 1 and confirm the same notes at a slower,
   swung rhythm. Stop afterward and return to Sound 8 / TONE, write off.

No separate ordinary playback recording is required for this composition check.
Exact recapture tests the joint stored state, and the independent BPM reading tests
tempo without modifying the restored swing value. Missing display confirmation
remains unevaluated; it is never inferred from backup bytes. Every unknown field stays
visible, and no numeric timing units are assumed.

- [Hash-bound plan](../experiments/joint-tempo100-swing9-plan-001/plan.json)
- [Registered target](../experiments/edited-joint-tempo100-swing9-001/joint-global-registration.json)
- [Compiler report](../experiments/edited-joint-tempo100-swing9-001/compile-report.json)
- After native decoding at threshold 0.0063:
  `python -m scripts.check_joint_tempo_swing_restore --displayed-bpm ACTUAL_BPM`

Completed: the user confirms the requested restore/display/playback checks and every
native byte matches. Public edits reproduce the accepted body in either order, and
an inverse edit recovers the genuine 137/6 state exactly. See
[results](joint-tempo-swing-results.md) and the [next volume probe](sound3-volume-probe-control.md).
