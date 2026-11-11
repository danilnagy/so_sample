# Recorded FILTER B counterclockwise probe

Current genuine state is the verified public-plan center63 return at pitch14 and
volume36. The [official control guide](https://teenage.engineering/guides/po-33/en)
assigns FILTER B to resonance. Its stored field remains unknown. This new probe
registers two third-primary candidate masks before recording: bits2..6 (0x7c)
and bits2..7 (0xfc). Neither bit7's role nor an endpoint value is assumed.

1. Keep Pattern1 / Sound3 / FILTER selected. Keep A and audio settings unchanged.
2. Start playback, hold WRITE, and slowly turn **only B fully counterclockwise**
   over about5 seconds. Hold WRITE3 more seconds with the knobs stationary.
3. Release WRITE, stop playback and ensure write is off. Save the complete backup
   as `experiments/event-062-a-sound3-filter-B-lock-down/capture.wav` at the
   established reduced level, with one second trailing silence.
4. Report the actual audible and display changes, including no change. Leave B
   at minimum and A untouched. Do not press keyboard keys or hold BPM/FX during
   the pass. No restore or separate playback recording is needed.

At the center cutoff, a resonance change may have no audible effect. There is no
required auditory outcome, numeric UI value, exact code, uniformity or zero
prediction. The checker retains no serialized change as a valid native result.

The two strict masks are tested separately against complete noncandidate state.
Pitch14, volume36 and stored A63 preservation are reported independently. A broader
FILTER snapshot allows A's second-primary high-four and the whole third byte;
broader primary/auxiliary changes remain separate alternatives. A coupled change
does not rescue strict B support. Both literal projections, bit7 values, changed
steps and any ramps remain in the report. Public filter guards remain unchanged
and will reject unfamiliar third-byte contexts rather than overwrite them.

The source backup preceded the already confirmed ordinary playback. This test
therefore includes that intervening playback plus the recorded B action; any
unrelated change is retained without attributing it solely to B. No field width,
resonance scale or resonance writer is inferred from a first pass.

- [Preregistration](../experiments/sound3-filter-B-minimum-registration-001.json)
- [Checker](../scripts/check_sound3_filter_B_probe.py)
- [Verified source results](generated-sound3-filter63-results.md)

After independent threshold0.0063 decoding, run
`python -m scripts.check_sound3_filter_B_probe`. Reports stay immutable and
hardware-unverified. All67 affected checks pass, including mask separation, bit7,
ramps, no change, coupled A updates, hidden state, stale hashes and public guard
rejection. Production code is unchanged since the full1,025-test run.

## Completed with a retained narrow-mask failure

The B minimum clears bit7 in the five Sound3 note cells; both projections become0
throughout. The0xfc mask preserves every noncandidate bit, while0x7c fails because
it excludes the actual change. Pitch14, volume36 and cutoff63 remain exact. The user
reports no audible change. See [results](sound3-filter-B-minimum-results.md) and
the [next maximum/minimum return](sound3-filter-B-range-control.md).
