# Drum copy adds sixteen shared references

The Sound1-to-Sound9 copy passes every registered preservation check. The normal
crossing decoder at0.0063 validates all **527 checksums**, with exact native re-encoding.
Only data under selector IDs **8..23** is added. The existing65536-code backing buffer,
melodic references, all16 patterns, selector order and every unrelated packet remain
identical. No new sample buffer is allocated in this capture.

All16 candidate destination groups populate, each with one9-byte reference to **owner0**.
The alternative predicting only the first group populated fails and is retained. The
Sound9 block mapping is supported by the isolated physical copy. Individual keyboard-key
order remains a hypothesis until a single-slice control identifies the changed record.

| Evidence | Result |
| --- | --- |
| Added data packets | 16 |
| Added native body bytes | 224, including headers/checksums |
| Frame end | 89620 |
| WAV SHA-256 | `9bafc45f6e12bae5cdcb1c80f60b57248cd3003144946dbf2b670cd20be7a34c` |
| Artifact SHA-256 | `dcebfbb1c93317bcdb7354febb30cb3d931757bd650921eab41017c69a1da8b8` |
| Native body SHA-256 | `f83e2157513a3ae344631366464e3a25363fc296900575d792139455b66b91a0` |
| Recording | Stereo PCM16/44100Hz,1130724frames,25.64seconds |
| Peaks | 0.16757/0.16055, no clipping indicators |

- [Original predictions](../experiments/drum9-copy-predictions-001.json)
- [Preservation, alternative hypotheses and all raw references](../experiments/drum9-copy-results-001.json)

Post-capture observation: second fields are4044,8088,...64704. The first field is0 in
selector8, then4045,8089,...60661 in subsequent records. Thus the observed second fields
advance by4044, and each subsequent first field is the previous second plus1. This
regularity was not preregistered. It does not establish a universal autoslice formula,
whether endpoints are inclusive, or how key order maps to record order. The final
second field equals the source Sound1 counter64704; sample-code content remains intact.

The project exporter now groups **all16 references under Sound9**, correcting the old
slot-minus-one lookup that would have labeled selectors9..15 as separate drum sounds
and omitted later Sound9 records from the sound view. Other drum blocks are explicitly
marked inferred/unverified. Unknown record shapes remain raw without fabricated fields.
The raw packet view continues to preserve every packet exactly. `sounds.json` now uses
schema version2; the export report uses read-only-project-export-0.3.

The current export is **experiments/exported-drum9-copy-001/project.json**, containing
all16 patterns, four melodic previews and144 bytes of raw Sound9 references. No drum
preview or writer is enabled; this physical copy is not a generated drum-edit restore.

The complete suite passes **366 tests in60.61seconds**, with Ruff lint/format checks
passing for114Python files. Tests retain the failed first-only alternative, reject
checksum-valid backing/pattern/opaque changes, preserve unknown drum record shapes and
verify that all16 records remain under Sound9 without contaminating Sounds10..16.

The next [single-slice minimum control](drum9-key1-trim-min-control.md) tests key1's
selector mapping and boundary fields with other slices, sounds and patterns preserved.
