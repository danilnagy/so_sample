# Known periodic sound control

Slot 8 was confirmed empty by the user. Use the ordinary sound
../calibration-source-001/tone-375hz.wav as the line-input sample: a 2-second
375 Hz tone with short fades and peak 0.25, not backup/restore data.

1. Keep Pattern 1's existing kicks at Steps 1 and 2. Stop playback and leave write mode off.
2. Connect computer output to the PO-33 line input. Open tone-375hz.wav in Audacity or
   your normal player, ready to play from its beginning.
3. Hold **record + key 8**, start tone playback, then release both buttons after the
   tone finishes. The [official guide](https://teenage.engineering/guides/po-33/en)
   specifies line-input recording when its cable is connected. Use normal sound sampling
   for this tone. If the device reports no available recording time, stop and report it;
   no other slot needs to be changed for this experiment.
4. Check that Sound 8 plays a steady tone. Do not trim or change pitch, filter or other
   sample settings. Return to **Sound 9, slice key 1**, with write mode off and playback
   stopped, to match the previous planned capture selection.
5. Reconnect your usual stereo backup recording path and save one complete dump as
   **capture.wav in this folder**, at the same reduced recording level. Leave Sound 8
   and the pattern unchanged afterward; no A-return is requested.

Report if sampling stopped early, memory was full, the tone was distorted, or another
control changed. An exact button-timed duration is not required. Corrected event-005-b-joint
is the reused before-state control; no fresh A is needed. Its waveform remains untouched.

Future analysis will check provenance, channel counts and the independent amplitude clock,
then examine periodicity in raw/staggered/differential views. Any period will be measured
and checked across separate windows. No internal codec, sample rate or expected state
offset is assumed, and repetition alone will not make a sample field writable.
