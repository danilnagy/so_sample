# Partial-tone backup validated

Source hash: dfcd59dfa2ae04973f49090b0997e7f1508aaf62e18a9293362240ad397e54f7.
The original stereo 44100 Hz PCM16 WAV is untouched. Peak levels 0.168793 left and
0.161041 right remain suitable, with no clipping. The user reports storage full and
about one second of the tone retained; neither exact stored duration nor native sample
format has been measured. No memory reset or clearing was requested.

At normalized threshold 0.0063, label counts are 2070730 left and 2070729 right, versus
1970367 each in corrected joint baseline. The added counts are 100363 and 100362.
Their difference is an explicitly retained endpoint, not corrected or padded. Both raw
channels first differ at index 829509. The independent amplitude clock again finds zero
label/quarter disagreements throughout its checked interior (waveform-probes-007.json).

An exact 520-increment repeating region is longer than in the previous recording, but
the prior capture also contains a shorter 520-period region. The new repetition is not
verified tone content. A diagnostic displacement of 100362 increments yields an exact
360932-increment shared suffix on both channels; no artifact was shifted or rewritten.
See ../tone-structure-001.json and ../../docs/tone-investigation.md.

Bounded CRC frame hypotheses failed independent validation. Seventeen one-block CRC16
hits all fail every one of 64 later blocks; no CRC32 hit occurs in the tested mappings.
These are discarded candidate models, not a discovered checksum or state image.

Next requested file is sample-playback.wav: a few seconds of ordinary Sound 8 playback
through the usual computer recording input, triggering melodic key 1 once with write
mode off and playback stopped. Return to Sound 9 slice 1 afterward. Keep the current
memory/patterns. This will verify the actual partial sample before assigning meaning
to backup periodicity. Full details are in playback-request.json.

Complete regression suite: 144 passed in43.73 seconds. Ruff lint/format checks pass.

## Sample playback received

The requested sample-playback.wav is now received, hash
23994e265f0479c49215d5401cb25c425bed8765cc43ff0afbc6a81987991197.
It is stereo44100 Hz PCM16,153056 frames (3.470658 seconds including silence), with
peaks0.06363/0.06079 and no clipping. Channels are highly correlated, as expected for
this ordinary sound, unlike the independent backup data channels.

10 ms RMS windows detect one audible region from1.31 to2.57 seconds, duration1.26s.
An interior sinusoid fit measures561.946Hz on both channels and explains ~99.93% of
their variance. Compared with the375 Hz input, the measured ratio is1.498523, or
+7.0025 semitones. Transposition/pitch settings are a plausible explanation, not an
independently observed button setting. Exact triggered note and pitch parameters were
not separately supplied.

Audible playback duration at this note is not native stored sample duration. Therefore
the earlier user estimate of partial storage must not be promoted to an exact one-second
sample length or decoded byte rate. The actual tone is confirmed, but no periodic backup
region has been uniquely identified as its encoded sample. Reports are playback-inspection.json
and playback-analysis.json. This closes the requested playback control.

Three new focused tests pass using known noisy/harmonic tones at44100/48000 Hz plus
invalid/no-signal inputs. Ruff checks pass. The last full suite remains144 tests before
these additions. New empty-state capture instructions are ../../docs/empty-baseline.md;
the old device state has not been automatically reset and all source WAVs are preserved.
