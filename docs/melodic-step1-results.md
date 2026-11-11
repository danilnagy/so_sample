# Melodic Step1 results

The user replied done to the requested single-note control and supplied the backup.
Using the fixed0.0063 threshold profile, all **511** native packet checksums validate.
Every [preregistered check](../experiments/melodic-step1-predictions-001.json) passes:
only Pattern1 changes, with unchanged samples, other patterns and opaque footer.

The complete Pattern1 byte differences are:

| Offset | Before | After | Observed region |
| ---: | ---: | ---: | --- |
| 6 | 00 | 0D | Step1 primary |
| 7 | 00 | F8 | Step1 primary |
| 8 | 00 | 83 | Step1 primary |
| 770 | 00 | F0 | Step1 auxiliary |

Only plain packet indices4 and7 differ from the verified empty baseline. The native
body SHA-256 is `c5a4889ed680aa756c0a04f2df92bd194319f79a6de1603a20558976043e67a9`.
Source WAV SHA-256 is
`4b5a18904460369f01abd6dce3d621b8264ccc1aee9f5b8d273e3c1db79dcb5f`.
See [registered results](../experiments/melodic-step1-results-001.json).

This supports a finer interpretation of the previously reported48-byte step row:
**16 sound-indexed cells of3 primary bytes**, with **one auxiliary byte per sound** in
the16-byte auxiliary row. The Sound3 control occupies primary offset3×(3−1)=6 and
auxiliary offset768+(3−1)=770. The earlier Sound9 controls occupy primary offset24 and
auxiliary offset776 at Step1. This slot correspondence is locally supported for Sounds3/9;
other sound slots and the packed primary/auxiliary bit meanings remain untested.

The old12-byte regions were diagnostic subdivisions, not verified voice records.
Reports retain those raw groupings and add three-byte cell inspection. No decoded pitch,
volume, gate, effects or sample-selection field is claimed. The Step2-only drum auxiliary
16/17 discrepancy remains unresolved.

The new `clone-step` operation copies both **complete opaque rows** of a source containing
one matching primary/auxiliary cell into completely empty target steps. It preserves the
source and rejects occupied targets, duplicate targets, empty sources and unsupported
source layouts. It changes no raw note fields. Genuine Sound9 Step1-to2 cloning reproduces
the corrected joint backup's entire packet body exactly, providing an independent guard.

The first generated pattern candidate duplicates this Sound3 source at Steps5/9/13 while
retaining Step1. It passes strict software waveform/count roundtrip and all packet checks.
The user confirms the generated pattern restore and expected playback worked;
the after-playback backup now matches the generated native body exactly. See
[the four-note restore test](native-pattern-restore-test.md).
