# Locate drum key1 and its minimum trim

Completed: key1 changes selector8 alone, preserving start0 and all unrelated data.
The observed second field127 rejects the exact79 prediction. See
[minimum results](drum9-key1-trim-min-results.md) and the
[first generated drum restore test](native-drum9-slice-end-restore-test.md). Original instructions follow.

The verified Sound9-copy capture is the baseline. Sound9 has sixteen9-byte references
under selector IDs8..23, all sharing owner0. One physical slice change will test individual
key ordering without editing samples or patterns.

1. Keep **Pattern1**, playback stopped and **write off**. Select **Sound9**, then tap
   **keyboard key1 once** to make it the last-triggered slice.
2. Select **TRIM / tri** with FX. Leave **knobA untouched**. Turn **only knobB slightly
   clockwise, then fully counterclockwise**. The initial movement ensures the control
   registers even if B was already at its minimum.
3. Return to **TONE**, select **Sound8**, and retain the successful capture settings.
4. Before any further audition or pattern playback, record a complete stereo backup as
   **experiments/event-016-b-drum9-key1-trim-min/capture.wav**.

Leave the new slice length in place. The [official guide](https://teenage.engineering/guides/po-33/en)
states that drum trim changes the last-triggered slice; knobB controls length. The
initial key1 tap is necessary to choose the slice, with write off to preserve the pattern.

Preservation checks allow only the first eight bytes of exactly one existing Sound9
reference to change. Its owner and size, the other15 references, all backing codes,
other sounds, patterns and every unrelated packet must remain identical. Both fields
may move if knobs couple; such changes are reported explicitly. Physical knobA remains
at its previous quarter position, which differs from the stored first-slice start0.

Separate hypotheses predict selector8 alone changes, its first field stays0, and its
second field becomes79 or at least moves below4044. The79 value comes from the earlier
melodic zero-start minimum and is an explicit transfer hypothesis, not a drum rule.
The broader decrease and exact79 prediction are evaluated separately. No general minimum,
endpoint inclusivity or autoslice formula is assumed.

- [Preregistered predictions](../experiments/drum9-key1-trim-min-predictions-001.json)
- Baseline WAV SHA-256: `9bafc45f6e12bae5cdcb1c80f60b57248cd3003144946dbf2b670cd20be7a34c`
- Baseline body SHA-256: `f83e2157513a3ae344631366464e3a25363fc296900575d792139455b66b91a0`
- Selector8 currently has reference `00000000cc0f000000`, packet index383.

No new restore is required. Use stereo PCM16/44100Hz without effects, and keep all existing
sounds present. Report any deviation; no generated drum edit is enabled by registration.
