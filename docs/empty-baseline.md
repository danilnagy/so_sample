# New minimal-state baseline

The previous series and original WAVs remain preserved. Playback of the retained Sound8
tone has now been measured, completing the requested control. This new series starts
from reset settings with all sound slots and patterns explicitly emptied. It does not
assume the internal flash or backup payload becomes zero or any particular size.

Keep a separate recovery copy of a backup you have already restored successfully before
replacing the device state. Record which recovery backup you used. Existing captures and
the last playback stay untouched. No computer tool has reset or modified the hardware.

Use the [official PO-33 guide](https://teenage.engineering/guides/po-33/en) for the device
operations below. Factory reset returns default settings; individual sound deletion frees
the sound memory, and pattern clearing is a separate operation.

1. **Factory reset:** remove the batteries, then hold **pattern + write** while inserting
   them. Complete clock setup if requested. Keep other settings/knobs/effects unchanged.
2. **Delete every sound slot, 1-16:** for each slot, select it with **sound + number**,
   release, then **hold record and press sound** to delete that selected sound. Work through
   all sixteen slots; deleting only patterns does not free sound recording memory.
3. **Clear every pattern, 1-16:** select each separately with **pattern + number** and
   release both buttons, then press **record + pattern** to clear the selected pattern.
   Release between pattern selections so this is not a multi-selection chain operation.
4. Select **Pattern1** and **Sound8**. Keep write mode off and sequencer playback stopped.
   Make no additional parameter adjustments. Report any step that behaved unexpectedly.
5. With the usual stereo backup connection and validated reduced recording level, save
   a complete backup as **experiments/empty-001-a/capture.wav**.
6. Without changing device selections, knobs, effects, tempo, patterns or recording settings,
   record another complete backup as **experiments/empty-001-a-repeat/capture.wav**.

Leave this empty state unchanged afterward. Sampling the next test tone waits until both
new captures have been inspected and their content/endpoints compared. Two consecutive
empty-state recordings test repeatability for this new state; earlier repeatability is
not assumed to cover every state or transfer length.

The existing reduced-level decoder threshold0.0063 is a starting analysis profile,
not a guaranteed parameter. New source hashes, channel lengths and uncertainty diagnostics
will be reviewed before accepting either capture as a regression fixture.

## Pair received and validated

Both new recordings match45033 complete labels per channel exactly, including the
canonical partial endpoint intervals. Independent waveform checks agree, and both WAVs
are registered without altering their source bytes. See ../experiments/empty-001-results.md
for thresholds, lower capture amplitude, hash pins and unresolved encoding limits.
The next control is in empty-tone-control.md; leave the baseline selections intact until
sampling Sound8 and keep Pattern1 empty.
