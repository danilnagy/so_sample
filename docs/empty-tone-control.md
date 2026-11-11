# First sound in the new minimal-state series

Both empty baselines now contain identical45033 complete labels per channel, including
matching partial final sign intervals at threshold0.0063. Keep these baselines as the
before-state; there is no need to reset or clear again for this step.

1. Keep Pattern1 empty, write mode off and playback stopped. Use the prepared ordinary
   sound **experiments/calibration-source-001/tone-375hz.wav** (2seconds,375 Hz).
2. Connect computer output to PO-33 line input. Open the tone in Audacity ready to start.
   Hold **record + key8**, start the tone, and release after it finishes. This records
   into melodic Sound8. The [official guide](https://teenage.engineering/guides/po-33/en)
   describes line-input sampling with this button combination.
3. Keep Pattern1 and Sound8 selected afterward, with write mode off/playback stopped.
   Keep the sample untrimmed and other controls unchanged. Save the backup before any
   additional audition; the existing baseline had no audition step.
4. Reconnect the usual PO-33 output-to-computer stereo recording path. Save a complete
   dump as **experiments/empty-001-b-tone/capture.wav** using current recording settings.
5. Without changing device state or levels, record another complete dump as
   **experiments/empty-001-b-tone-repeat/capture.wav**.

Leave this one-tone state unchanged afterward. Exact sampling-button timing is not
required. Report if sampling ends early or any other settings/events change. These
transfers should be more manageable with one sample, but their exact lengths are not
predicted or assumed. No added pattern event is requested yet.

The current capture peaks (~0.067/0.064) are below the previous series but unclipped and
validated. Both complete label streams and independent quarter signs match. The canonical
decoder threshold stays0.0063. Lower thresholds are not automatically better: the repeat
can acquire a noise gap or extra partial endpoint interval. No gain adjustment is required
for the validated empty captures; the next recordings will be checked again.

The earlier0.004 failure was subsequently traced to the0.1 decoder's virtual origin,
not an established physical noise gap. Decoder0.2 resolves it without trimming audio;
see transport.md and empty-structure-002.json. Lower thresholds can still change partial
endpoints, and the canonical profile stays0.0063.

## Pair completed

Both requested one-tone recordings now match exactly, including retained partial endpoints.
The source WAVs and independent waveform reports are preserved; details are in
minimal-one-tone.md and ../experiments/empty-001-b-tone/validation.md. The next capture
copies stored Sound8 into empty Sound1, retaining the source and avoiding another ADC
recording. Instructions are ../experiments/empty-001-c-copy-to-1/README.md.
