# Recovery-history capture retained as a confounded control

The user reported deleting Sound8 accidentally, copying Sound1 back into8, then copying
8 into2. Those are the actual reported operations. The original prediction assumed only
one source8-to2 copy, so this capture is not eligible as a clean causal test of that action.
It is preserved and remains useful for observational structure checks.

Original WAV SHA-256:7acb719c345ba68f142fe9872662bf603b108d5b3671e82c49fa61320c1c8d0e.
Stereo44100 Hz PCM16,1142189 frames,25.899977s including recording margins, peaks
0.16806/0.16095 and no clipping. Source samples are unchanged.

## Acquisition fix

Decoder0.1 failed at threshold0.0063 because the first significant samples are negative
at frame77528, about1.76 seconds into the file. Its implicit negative transition at file
zero counted that silence as a huge sign interval. This was a software acquisition bug,
not evidence of a corrupted backup or a physical gap inside the data.

Decoder0.2 places the approximate negative origin at the first thresholded sample. It
does not trim source audio or relax the guard for actual long crossing gaps. The corrected
decode at the same0.0063 threshold preserves178900 complete labels per channel and partial
final intervals left[0], right[1]. The independent amplitude-derived clock agrees with
all four quarter signs in the tested interior (../waveform-probes-013.json).

All154 regression tests pass after the decoder change, including existing genuine-capture
symbol goldens and hardware-validated reconstructed waveform checks. A new dedicated
real-capture check also passes. Saved0.1 NPZ artifacts and original WAVs remain unchanged;
fixture current-version expectations retain their originally reviewed version provenance.

## Predictions observed under the deviation

Relative to the preceding Sound1/8 capture, complete counts increase by32 on both
channels. First strict changes are177093 left and177092 right. Both fall in the registered
inline window[177085,177121); neither falls in the front-table window. Both counts fit
the registered small-growth range. All six registered anchors at90000/120000/150000
increments match at their original positions. No prediction or alignment was revised.

These are observational matches only. Deleting/recreating the source can alter allocation
or later serialization, so the original single-action hypothesis is not declared confirmed
or causally falsified. Authoritative reproducible report: ../second-copy-observations-002.json.
Initial audit report001 is retained alongside it.

Next requests a fresh clean pair: delete only Sound2 and record the actual recovered
Sound1/8 before-state, then perform only copy8-to2 and record the after-state. Paths are
../empty-001-copy2-clean-a/capture.wav and ../empty-001-copy2-clean-b/capture.wav.
Full instructions are ../../docs/clean-copy2-control.md. No new ADC recording or reset is
needed, and the recovered before-state is not silently assumed identical to originalC.
