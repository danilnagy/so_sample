# Add the first calibrated Sound10 drum note

Completed: all preservation checks pass with543 valid checksums. Sound10 maps to cell10,
primary0df883 matches the Sound3 comparison, but auxiliary10 differs from predictedF0.
See [results](drum10-note-results.md) and the
[next generated drum-cell test](native-drum-cell-copy-restore-test.md). The original
predictions and physical instructions follow unchanged.

Use the current accepted cross-drum-copy device state. Sound10/key1 is the short
start4045/end6045 tone. Pattern1 has Sound3 notes at Steps1/5/9/13 and Sound2 at Step9;
all Sound10 pattern cells are empty in the verified baseline. Preserve those existing
notes and both knobs, effects, tempo and pattern chain.

1. Retain **Pattern1**, playback stopped and **write off**. Select **Sound10 / TONE**
   and tap **keyboard key1 once** to select the last-triggered slice.
2. Press **write**. **Step1 should be unlit for Sound10**. Tap **Step1 once** to add
   its note, then press **write** again to exit. Keep the existing Sound3 Step1 note
   and every other note in place. If Step1 is already lit, exit write without toggling
   it and report that state.
3. Select **Sound8 / TONE**, playback stopped and write off, with all knobs and recording
   settings unchanged. **Before playing the pattern**, record a full stereo PCM16/44100Hz
   backup as **experiments/event-020-b-drum10-key1-step1/capture.wav**. Let the full dump
   finish and retain a second of silence before stopping the recording.

Leave the new Sound10 note in place and report deviations. The control uses the existing
successful reduced recording levels. Step editing follows the
[official PO-33 guide](https://teenage.engineering/guides/po-33/en).

The checker separates preservation from untested drum encoding hypotheses. One
previously empty raw cell may change within Step1's primary[0:48] and auxiliary[768:784]
rows. The existing Sound3 neighbor's bytes[6:9] and byte770 must remain identical.
Every other step, footer, other15 patterns, all sample/reference packets and every
other plain packet must remain unchanged; exactly543 packets/end89844 are required.

Separate predictions test whether Sound10 uses cell10, primary[27:30]/auxiliary777;
whether key1 producesF0 like the melodic controls; whether primary data matches
Sound3's0df883 or Sound2's0d2831; and whether only native packets4/7 change. The two
primary comparisons are mutually exclusive and may both fail. An unchanged zero
auxiliary or a different primary is reported independently, without changing the saved
prediction or forcing data into the expected value. Another cell location is a mapping
failure even if broad row preservation holds. No drum pattern writer or keyboard-key
projection is enabled in advance.

- [Preregistered predictions](../experiments/drum10-note-predictions-001.json)
- [Experiment metadata](../experiments/event-020-b-drum10-key1-step1/experiment.json)
- [Accepted baseline](native-cross-drum-slice-copy-results.md)
- Baseline WAV SHA-256: `ac23213297cb3a1d0b56515bbb78bb5485b72cf5e420376ea591ae11f0d647cc`
- Baseline body SHA-256: `846092c09285da128689493f2a332fef8e0c22ac93fb710f9e0b994661fe971e`

If normal capture decoding fails, retain that attempt. Any established waveform-only
clock fallback must use its independent acquisition/pre-frame alignment, without
expected note bytes, a target body or checksum-guided repairs.
