# Measure the retained full tone

The copy-based return reproduces the original Sound3 backup content. We now need one
ordinary audio recording of that tone from the current cleared-state series. The previous
playback recording came from the older partial, memory-full control and is kept separate.

1. Keep **write mode off** and the sequencer stopped. Select **Sound3** with **sound + 3**.
   Retain TONE and all current knobs/settings.
2. Start recording the PO-33's usual line output in Audacity; allow a short silence.
3. **Tap key1 once**, release, and let the sound finish completely. Keep recording for
   roughly one second afterward, then stop. Capture the whole sound, not a data dump.
4. Export the original recording as stereo PCM WAV to
   **experiments/empty-001-h-sound3-copy-return/sample-playback.wav**.
5. Reselect **Sound8** afterward, leaving sounds1/2/3/8 and Pattern1 unchanged.

Selecting sounds and triggering a melodic key follow the
[official guide](https://teenage.engineering/guides/po-33/en). The supplied input tone was
375 Hz, but melodic-note/default-pitch behavior can transpose it. We will measure audible
frequency and duration rather than assuming that playback is untransposed native PCM.
No further backup, sampling or trimming is requested for this observation.

Completed: the recording is valid, with1.25s audible tone at561.954Hz. See
[playback results](minimal-tone-playback-results.md). Subsequent packet decoding now
supports a generated trim experiment; see [the hardware test](native-trim-restore-test.md).
