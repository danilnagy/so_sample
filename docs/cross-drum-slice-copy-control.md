# Copy one calibrated slice between drum sounds

Completed: all preservation checks and all three saved hypotheses pass with543 valid
checksums. Sound10/key1 maps to selector24 and receives the exact Sound9/key1 reference,
while every other plain packet remains identical. See [results](cross-drum-slice-copy-results.md)
and the [next generated restore test](native-cross-drum-slice-copy-restore-test.md).
The original registration and physical instructions follow unchanged.

The clean Sound10-copy capture is the baseline. Sound9/key1 stores start0/end2000/owner0;
candidate Sound10/key1 (selector24) stores start0/end4044/owner0. The Sound10 block is
known, but its individual keyboard ordering still needs a direct control.

1. Keep **Pattern1**, playback stopped and **write off**. Select **Sound9**, then tap
   **keyboard key1 once** to choose the last-triggered source slice.
2. Hold **write + sound**. Press and release **10**, keeping **write + sound held**.
   Then press **1** and release all buttons. This targets **Sound10/key1**.
3. Reselect **Sound8 / TONE** without moving either knob or changing the successful
   recording setup.
4. Before further audition or pattern playback, record a complete stereo backup as
   **experiments/event-019-b-copy-drum9-key1-to-drum10-key1/capture.wav**. Let the entire
   dump finish and leave a second of silence before stopping the recording.

Leave the copied slice in place and report deviations. The
[official guide](https://teenage.engineering/guides/po-33/en) describes copying the
last-triggered drum slice using write+sound, then a destination drum sound key9..16,
followed by a destination slice key1..16. This is a slice copy rather than the earlier
single-destination-key whole-sound operation. No restore is needed.

Checks allow only the first eight bytes of exactly one existing Sound10 reference to
change. Its size9 and owner0, the other15 destination records, every Sound9/source
record, all backing codes, melodic sounds, patterns and unrelated packets must remain
identical. New allocations/resized packets are deviations to report, not to hide.

Separate hypotheses predict Sound10/key1 maps to selector24, its reference becomes the
source's exact **00000000d007000000**, and only packet415 bytes4/5 change from
4044 to2000. A different changed selector remains a mapping failure even if the copy
contents match. This tests reference copying without assuming Tone/filter rendering
parameters are transferred. No Sound10 writer or preview is enabled in advance.

- [Preregistered predictions](../experiments/cross-drum-slice-copy-predictions-001.json)
- Baseline WAV SHA-256: `073011e3cdd30f3bb376396385a154ec581d24412c0f93362d189e2e8126e804`
- Baseline native body SHA-256: `9e2801c1d2e76144a88ea71c05cc69e0be58476d077305abb4997c2fb9d64323`

Use stereo PCM16/44100Hz without effects. The source selection key1 tap precedes the
copy; subsequent audition or pattern playback waits until after the new backup.
