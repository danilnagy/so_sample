# New minimal-state baseline validated

Both requested recordings are valid stereo44100 Hz PCM16 WAVs with different source
hashes and durations, but identical decoded complete phase streams at threshold0.0063:
45033 labels per channel, zero changes, zero length differences and no applied shift.

| Capture | Source SHA-256 | Frames | File duration |
| --- | --- | --- | --- |
| empty-001-a | fcd6d5e6772440342c1d19eee3c3c0a3f3064541ed21b6dfcc6964aa2aec1309 | 358047 | 8.118980s |
| empty-001-a-repeat | 65d8145f519c71bec0162fb38c6fe134008a096cf46183be233980ff34259a57 | 377760 | 8.565986s |

The matching partial endpoint signs are explicitly retained: left[0], right[0,0].
These are residual sign intervals, not extra verified state bits. No padding/trimming
was used to make counts match. The current encoder refuses nonempty incomplete final
intervals, so no reconstructed restore was generated from this pair.

Peaks are~0.0669 left/~0.0640 right, lower than the old populated-state series but
unclipped and sufficient for the canonical threshold. The independent amplitude clock
agrees with all complete labels and all four quarter signs in both checked interiors.
Reports: empty-001-comparison.json, waveform-probes-008.json and009.json.

The repeated prefix retains periods512/128, breaking at index8185 on both channels;
this is repetition evidence, not a verified payload boundary. The active transfer is
roughly5.76 seconds. The baseline is substantially smaller than old sample-containing
states, consistent with the requested minimal-state procedure. Exact reset/deletion
button logs and the recovery-backup ID were not supplied; those remain unknown.

Report empty-structure-001.json tests four single-state views and both channels. None
of8448 decimated lane mappings supports a degree<=32 recurrence in the chosen training/
holdout windows. Fits of undecimated lanes have degree253-257. Lag scans beyond the
known prefix show no long520 repetition here; the longest tested lag520 run is9 pairs.
These finite negative probes do not establish encryption or an all-zero state image.

Threshold sensitivity is recorded instead of silently selecting a favorable profile.
At0.0025 the repeat retains identical complete labels but an extra right partial sign.
At0.004 it fails on an isolated long crossing gap; at0.0063 both complete labels and
partial endpoints match. Canonical0.0063 therefore remains the explicit analysis profile.
No lower gain or lower threshold is requested.

Subsequent acquisition audit corrected the0.004 failure explanation: the0.1 decoder
could count leading silence from an invented negative origin at file zero. With0.2,
empty-001-a-repeat decodes at0.004 and matches complete labels/partial endpoints too.
The old diagnostic report is preserved; empty-structure-002.json is the new versioned
recheck. The0.0025 extra partial endpoint remains, and canonical0.0063 is unchanged.

The new pinned capture-pair test passes, checking source/symbol hashes, counts and partial
endpoints. Ruff lint/format checks pass. Sources remain untouched. The last full suite
was144 tests before subsequent playback/empty-state additions; it is not relabeled as
a newer full-suite run.

Next requested control: record the full375 Hz calibration sound in empty Sound8 while
retaining empty Pattern1, then record two consecutive one-tone backups. No further reset
or fresh empty-state capture is needed. See ../docs/empty-tone-control.md and folders
empty-001-b-tone / empty-001-b-tone-repeat. No sample/pattern field is writable yet.
