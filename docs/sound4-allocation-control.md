# Record a second independent sample into empty Sound4

Completed: all controls and allocation hypotheses pass with679 valid checksums.
Sound4 owns a new32768-code buffer; every previous record/pattern is unchanged. See
[results and sample analysis](sound4-allocation-results.md) and the
[next second-owner copy](sound4-to5-copy-control.md). Original predictions and recording
instructions follow unchanged.

Sound4 is empty in the verified baseline. The existing750Hz sample lives in owner0's
65536-code buffer; Sounds1/2/3/8 and the drum references share it. Pattern1 contains
Sound10/key1 at Step1 and key2 at Step9 alongside the preserved melodic notes. Keep
this state, both knobs, effects, tempo and pattern chain unchanged.

The ordinary input file is
**experiments/calibration-second-owner-001/tone-1000hz-0p5s.wav**: a half-second1000Hz
tone, stereo PCM16/44100Hz with identical channels, amplitude0.25 and short edge fades.
It is distinct from the existing shared tone. Its exact WAV SHA-256 is
`61e447697569c47fc4f9471ece913d16c829d488cc56285836c934452084509e`.

1. Keep **Pattern1**, playback stopped and **write off**. Connect the computer output
   to the PO-33 line input using the previously successful sampling path. Open the tone
   ready to play and keep the established sampling playback level.
2. Hold **record + keyboard key4**, play the complete half-second tone, then release
   after it ends. This records a fresh sample into **Sound4**. Button timing is not
   treated as an exact length measurement. Do not move either knob.
3. Select **Sound8 / TONE**, playback stopped and write off. Reconnect the proven
   PO-33-output-to-computer stereo backup path. **Before further audition or pattern
   playback**, save a full stereo PCM16/44100Hz dump at the successful reduced recording
   levels as **experiments/event-022-b-record-independent-sound4/capture.wav**. The dump
   may be longer; let it finish completely and retain a second of trailing silence.
4. After saving, select **Sound4 / TONE**, write off, and tap **keyboard key1** to
   confirm a clear tone. Return to Sound8/TONE and report the tone check and any early
   recording stop, memory warning or deviation. Keep the new sample present.

The line-input sampling combination follows the
[official guide](https://teenage.engineering/guides/po-33/en). A fresh recording into
an empty slot is needed to observe allocation and ownership; current sample-copy
operations create references to existing data.

The core checks require a complete checksum-valid frame, the registered empty Sound4
baseline and unchanged patterns/selector order. New data must appear under Sound4's
selector3. Packet count, allocation padding and exact manually gated sample length are
not assumed. Other sound/global changes are reported as separate preservation hypotheses
so that possible relocation or allocator bookkeeping is visible.

Separate hypotheses predict a Sound4 self-owned buffer (owner3 and more than9 payload
bytes), zero start, a positive endpoint within its new buffer, only selector3 data changes,
an unchanged owner0/header/code buffer and all other sound records, and only new Sound4
data packets added. New sample codes should differ from the existing owner's codes.
A different owner/layout/global change is reported independently without fitting the
decoder or repairing data. No allocation/resizing writer is enabled from one recording.

- [Preregistered predictions](../experiments/sound4-allocation-predictions-001.json)
- [Experiment metadata](../experiments/event-022-b-record-independent-sound4/experiment.json)
- [Input tone metadata](../experiments/calibration-second-owner-001/source.json)
- [Verified key2 baseline](drum10-step9-key2-results.md)
- Baseline WAV SHA-256: `853d6d6249a98538ab4200b1067d216636b6e796044dc01bf1993c2b80061114`
- Baseline body SHA-256: `1ca3319167b14624b25a4bddf88abf4263040d2491269cb20ef188841d2955fb`

If decoding fails, retain the attempt. Established waveform-only recovery may use
pre-frame acquisition evidence, never predicted ownership, sample length or target bytes.
