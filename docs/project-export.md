# Read-only project export

`export-project` creates a readable research project from a checksum-validated symbol
artifact and its matching original WAV. It preserves every raw packet, the complete
native body and both original source files, while exposing pattern JSON and supported
sample previews. It writes only to a fresh folder and refuses existing paths and
mismatched capture identity before creating output.

The current hardware-verified removal state is available at
**experiments/exported-project-001/project.json**. Its native body SHA-256 is
`1e493f1495ecf2dc68077a35ae97b8883acbe96b94d0798427a9f3f990a1761a`.

| File | Content |
| --- | --- |
| `project.json` | Versioned read-only manifest, provenance, native-frame identity, views and limits |
| `sounds.json` | Sixteen sound-slot views, raw packet indices, preview support and backing-owner relationships |
| `patterns/01.json` through `16.json` | Complete raw pattern bytes, hashes, observed cells and narrowly calibrated keyboard-key projections |
| `samples/01.wav`, `02.wav`, `03.wav`, `08.wav` | Zero-start melodic previews, mono 48 kHz float WAV, retaining gain |
| `source/capture.wav` | Byte-identical original stereo backup |
| `source/capture.symbols.npz` | Byte-identical supplied artifact, including its decoder and transformation provenance |
| `source/packets.json` | Every native packet in order, with opaque tag/payload values and body hash |
| `source/native-body.bin` | Exact encoded native frame body; acquisition/carrier remain in the source files |
| `export-report.json` | Source checks, exact packet-view roundtrip, exported-file hashes and preview list |

There are 26 hashed content files plus the export report. Source hashes and all exported
file hashes have been checked. Packet JSON reconstructs the whole encoded native body
exactly, preserving unknown tags and payloads. This is a representation consistency check,
not permission to restore arbitrary edited packet JSON.

Pattern 1 shows Sound 3 keys 1/2/7/16 at Steps 1/5/9/13 and Sound 2 key 1 at Step 9.
Only the calibrated Sound 2/3 primary/auxiliary combinations receive a keyboard-key
projection. Unknown combinations retain their raw values without invented semantics.
The primary note parameters remain opaque.

Sounds 1/2/3/8 share backing owner 0. Their previews use the existing zero-start extraction
policy and nominal sample rate; Sound 3 exports 16,384 frames at 48 kHz. Sequencer pitch
is not applied to sample previews. Unsupported melodic layouts and drum data are retained
in the raw packet view with an explicit preview status. Nonzero start, drum slices,
allocation and general editable parameters remain under investigation.

This milestone supplies the read-only project representation. JSON import, a graphical
editor and arbitrary state edits are not implemented. The export report remains
`hardware_verified: false`: producing these files is not a new hardware restore. The
source state's separate [hardware evidence](native-sound-cell-removal-results.md) is preserved.

The subsequent nonzero-start control has a separate export at
**experiments/exported-start-project-001/project.json**. Its raw frame and pattern views
are preserved exactly; Sound 3's unresolved nonzero-start layout is marked unsupported
for preview, while Sounds 1/2/8 still export. The baseline export above is retained.
See [start-control results](sound3-start-results.md).

The subsequently verified fixed-start window can now be included with explicit
`--calibrated-windows` opt-in. The current export at
**experiments/exported-verified-window-001/project.json** includes all four previews and
the declared half-open Sound 3 selection policy. Default behavior still retains unsupported
nonzero layouts raw. Other starts remain unsupported. A separate
[guarded edit plan](edit-plans.md) is now available; exported views themselves remain read-only.

The subsequent second-start window is now independently hardware verified. The explicit
`--calibrated-windows` option supports both discrete observed starts11716/31393 within
their separate local endpoint intervals. The current export is
**experiments/exported-two-start-window-001/project.json**, sourced from the clean retry,
with previews1/2/3/8 and all16 patterns. Sound3 reads[11716:19716] under the declared
half-open convention. Interpolated starts and drum previews remain unsupported. See
[second-start hardware results](native-quarter-window-results.md).

The new Sound9-copy export is **experiments/exported-drum9-copy-001/project.json**.
The corrected sound view groups selector8..23 under Sound9, retaining all sixteen raw
reference records. It does not treat selectors9..15 as separate Sounds10..16. Other
drum-block mappings are labeled candidates, and keyboard order remains unverified.
Drum audio previews stay disabled; melodic preview behavior is unchanged. Sound-view
schema version2 records these distinctions. See [drum-copy results](drum9-copy-results.md).

The key1 minimum control now independently maps Sound9/key1 to selector8. Its sound-view
entry carries `keyboard_key: 1` and `keyboard_order_status: observed_key1_trim_control`;
the other15 keyboard positions remain unverified candidates. The current export is
**experiments/exported-drum9-key1-min-001/project.json**. It still provides no drum audio
preview. The first endpoint-edit candidate has a separate explicitly unpitched preview
and awaits a device test. See [key1 minimum results](drum9-key1-trim-min-results.md).

The first drum endpoint edit now passes its separate device test. Export can explicitly
include **only Sound9/key1** with **--calibrated-drum-slices**, separately from the existing
`--calibrated-windows` option for Sound3. The current export is
**experiments/exported-verified-drum9-slice-001/project.json**, with all16 patterns,
four melodic previews and the2000-code drum preview at `samples/09-slice-01.wav`.
Default exports still include no drum audio previews. Unknown calibrated contexts stay
raw with a reason. No other drum keys or slots are previewed.

Drum previews use unpitched/unscaled raw-code extraction under the explicit half-open
selection policy. `preview_drum_slices` records each sound/slice/file mapping separately
from melodic `preview_sound_slots`; the report version is read-only-project-export-0.4.
All raw/native and source-file preservation checks remain required. See
[hardware and preview results](native-drum9-slice-end-results.md).

The key2 control now directly maps Sound9/key2 to selector9. Its raw-view entry is marked
`observed_key2_trim_control`, alongside the previously observed key1 mapping. The current
export is **experiments/exported-drum9-key2-min-001/project.json**. The optional project
drum preview remains limited to accepted key1 while the first generated key2 edit awaits
its device test. A standalone experimental key2 preview accompanies that candidate.
The library permits the separate calibrated key1/key2 intervals; unknown other14
references still prevent speculative preview. See [key2 results](drum9-key2-trim-min-results.md).

The key2 edit now has matching hardware evidence. Explicit **--calibrated-drum-slices**
opt-in exports both controlled keys1/2, each under the separate fixed-start interval and
shared-owner context guards. The current export is
**experiments/exported-verified-drum9-slices-001/project.json**, with four melodic previews,
two drum-slice previews and all16 patterns. Default drum preview behavior remains off.
No other drum key/slot is previewed. See [key2 hardware results](native-drum9-key2-end-results.md).

The two preview files are `samples/09-slice-01.wav` and `samples/09-slice-02.wav`.
Sound9 reports `preview_slice_keys: [1,2]` and per-slice preview metadata. Both are
unpitched/unscaled half-open raw-code selections; exact device endpoint inclusivity and
rendering parameters are not inferred. Export-report version is read-only-project-export-0.5.

The Sound10 copy now independently confirms selector24..39 as its block. Sound10 is
grouped with all16 raw references and `observed_sound10_copy_block`; its individual key
mapping remains unverified. Sound11..16 still carry candidate mappings, and no Sound10
audio preview is enabled. The current export is
**experiments/exported-drum10-copy-002/project.json**, retaining all16 patterns and the
existing four melodic/two Sound9 previews. Report version is read-only-project-export-0.6.
See [Sound10 results](drum10-copy-results.md).

Identical mono preview arrays now reuse the same encoded WAV bytes within one export,
including header metadata. This avoids libsndfile PEAK timestamp differences between
aliases when output generation crosses a second. Audio samples and selection policies
are unchanged; preview hashes across separate runs may still reflect creation timestamps.

The physical single-slice copy now independently maps Sound10/key1 to selector24. Its
record carries `keyboard_key: 1` and `observed_key1_slice_copy_control`; other15
Sound10 keyboard positions remain unverified. The current export is
**experiments/exported-cross-drum-copy-002/project.json**, with all raw/source data,
all16 patterns and existing four melodic/two Sound9 previews. Sound10 receives no
audio preview. Report version is read-only-project-export-0.7. See
[cross-drum results](cross-drum-slice-copy-results.md). A separate bounded copy plan,
rather than edited view JSON, supplies the next generated restore candidate.

That generated nonzero-start copy now has matching hardware recapture and confirmed
tone checks. Explicit **--calibrated-drum-slices** can include **Sound10/key1** at
either accepted copied window[0:2000] or[4045:6045], with the shared local-copy guards
and literal other15 destination references. Other Sound10 windows/keys receive a
raw view and unsupported-preview reason. Default drum preview remains off.

The current export is **experiments/exported-verified-cross-drum-copy-001/project.json**,
with four melodic previews and drum previews Sound9/keys1/2 plus Sound10/key1. The
nonzero Sound10 file `samples/10-slice-01.wav` equals `samples/09-slice-02.wav` byte for
byte; it contains4096FLOAT frames at48kHz under the explicit unpitched/unscaled half-open
policy. Other Sound10 keyboard mappings remain unverified. Report version is
read-only-project-export-0.8, with29 hashed content files. See
[hardware results](native-cross-drum-slice-copy-results.md). Export reports remain
software-only; the next physical drum-note capture does not broaden pattern editing
or key projections in advance.

The first physical drum note now observes Sound10/key1 at Pattern1/Step1 as primary
**0df883** and auxiliary **10**. The current export is
**experiments/exported-drum10-note-001/project.json**, retaining all raw/source data,
all patterns and four melodic/three drum-slice previews. Exact observed Sound10 pairs
carry **calibrated_drum_slice_key: 1**, separately from melodic keyboard-key projections;
unknown drum auxiliary/primary pairs retain their bytes with no slice-key projection.
Primary parameters and auxiliary upper-nibble meaning remain opaque. Report version is
read-only-project-export-0.9. See [drum-note results](drum10-note-results.md). Its first
generated copy plan awaits a separate device restore; exported JSON stays read-only.

That first generated drum-cell copy now has matching hardware evidence and confirmed
grids/playback. The current export is
**experiments/exported-verified-drum-cell-copy-001/project.json**, with Sound10/key1
events at Steps1/9, all prior melodic events, four melodic/three drum previews and every
raw/source packet intact. Export-report version stays0.9 and all29 content-file hashes
have been checked. Export reports remain software-only, separate from
[hardware acceptance](native-drum-cell-copy-results.md). A hypothetical key2 auxiliary11
receives no slice-key projection before its independent physical control.

The physical key2 control now independently observes the exact Sound10 pair0df883/11.
The current export is **experiments/exported-drum10-key2-note-001/project.json**, with
recorded key1 at Step1 and key2 at Step9, all melodic events, existing previews and raw
sources intact. Only primary0df883 paired with auxiliary10 or11 receives a recorded
drum-key projection; unobserved values stay raw. Sound10/key2's sample-reference selector
remains unverified and receives no keyboard mapping or preview. Report version is
read-only-project-export-0.10. No key2 writer is introduced. See
[key2 results](drum10-step9-key2-results.md).

The second independent recording adds a new self-owned Sound4 buffer with32768 codes,
owner3 and stored endpoint28608. The current export is
**experiments/exported-second-owner-001/project.json**, with previews1/2/3/4/8 and
the existing three drum previews, all16 patterns and exact raw/source data. Sound4's
`samples/04.wav` has58590FLOAT frames at48kHz under the existing zero-start endpoint
policy. Its entire buffer and nonzero code tail beyond the endpoint remain in the raw
view. There are30 hashed content files; report version stays0.10. No allocation or
resizing writer is enabled. See [allocation results](sound4-allocation-results.md).

The subsequent physical Sound4-to5 copy adds only a nine-byte owner3 reference. The
current export is **experiments/exported-second-owner-copy-001/project.json**, using
the verified analysis003 threshold0.004 artifact, independently corroborated by fixed
profiles0.01/0.02. Its source WAV is a byte-identical canonical copy of the preserved
uploaded `po_33_61.wav`. Six melodic previews now include Sound5; `samples/04.wav` and
`samples/05.wav` are byte-identical. All31 content hashes and every raw/source packet
are preserved; report version stays0.10. See [copy results](sound4-to5-copy-results.md).
Overwrite ownership and allocation policies remain unverified.

The subsequent re-recording grows Sound4 to73728 codes and transfers the complete old
32768-code buffer to Sound5/owner4. The current export is
**experiments/exported-shared-owner-growth-001/project.json**, with owners0/3/4,
six melodic/three drum previews, all patterns and exact raw/source data. Sound4's
147719-frame preview contains the new1250Hz sample; Sound5's58590-frame preview retains
the old1000Hz sample. Raw tails remain preserved in the native view. All31 content-file
hashes are checked; reports remain software-only. See
[ownership-transfer results](shared-sound4-rerecord-results.md). Allocation selection and
capacity shrink/reuse still need independent evidence.

The subsequent shorter recording now demonstrates shrink to32768/end30912 for
Sound4 while retaining Sound5's complete buffer. The current export is
**experiments/exported-unshared-shrink-001/project.json**, with six melodic/three
calibrated drum previews and31 checked content files. All raw records and source files
remain exact. See [shrink results](unshared-sound4-shrink-results.md). The separate
[generated growth backup](sound4-generated-growth-control.md) is a pending hardware
experiment; it does not make project JSON writable or introduce a general allocator.

The generated growth is now accepted with an exact hardware recapture. The current
read-only export is **experiments/exported-generated-sound4-growth-001/project.json**,
with the new3.08second1750Hz Sound4 preview, retained Sound5, six melodic/three drum
previews and31 checked content files. Every raw/source packet matches the generated
target. Separate hardware acceptance records the manual result; export reports remain
software-only. See [growth results](sound4-generated-growth-results.md). The
[generated shrink candidate](sound4-generated-shrink-control.md) is awaiting its
hardware test, and project JSON remains read-only.

The shrink target is now accepted with an exact hardware recapture. The current
read-only export is **experiments/exported-generated-sound4-shrink-001/project.json**,
including the new1.32second2250Hz Sound4 preview, retained Sound5 and every raw/source
record. Six melodic/three calibrated drum previews and31 content-file hashes pass.
Separate hardware acceptance records the manual result (sound4-generated-shrink-results.md).
The pending Sound6 creation candidate has no hardware recapture yet; project JSON
remains read-only and no public allocator is introduced.

The Sound6 creation is now accepted with an exact hardware recapture. The current
read-only export is **experiments/exported-generated-sound6-create-001/project.json**,
with the new1.32second500Hz Sound6 preview, all prior sounds/patterns and every raw/source
record. Seven melodic/three calibrated drum previews and32 content-file hashes pass.
Hardware acceptance is separate from the software export report
(sound6-generated-creation-results.md). The next generated Sound7 reference copy is
pending device testing; project JSON remains read-only.

The generated Sound6-to7 reference copy is now accepted with an exact hardware
recapture. The current read-only export is
**experiments/exported-generated-sound6-to7-copy-001/project.json**, with eight melodic
and three calibrated drum previews, every raw/source record and33 checked content
files. `samples/06.wav` and `samples/07.wav` are byte-identical; both resolve owner5's
unchanged full buffer. See [copy results](sound6-to7-generated-copy-results.md).
The next physical owner-deletion control is pending; project JSON remains read-only.

The physical shared-owner deletion now clears Sound6 and transfers its full sample to
self-owned Sound7. The current export is
**experiments/exported-shared-sound6-deletion-001/project.json**, with seven melodic/
three calibrated drum previews and32 checked content files. Sound7's decoded preview
PCM equals its prior shared window exactly; WAV headers can contain new export
timestamps, so PCM rather than cross-export file identity is checked. Every raw/source
record is preserved (shared-sound6-deletion-results.md). The next last-owner deletion
control is pending. Project JSON remains read-only; the separate guarded copy edit
plan reproduces a previously accepted WAV without changing export schema/version.

The final-owner deletion returns the entire native body to the pre-creation state.
The current export is **experiments/exported-unshared-sound7-deletion-001/project.json**,
with six melodic/three calibrated drum previews and31 checked content files. Sound6/7
are empty, every prior sound/pattern remains intact, and all source/raw records are
preserved (unshared-sound7-deletion-results.md). The next odd-page Sound6 candidate
is awaiting device testing. Project JSON remains read-only; copy/deletion edits use
separate guarded plans, with unchanged export schema/version.

The nine-page Sound6 sample is now hardware-accepted with exact retained capacity and
codes. The current export is **experiments/exported-sound6-nine-pages-001/project.json**,
with seven melodic/three calibrated drum previews and32 checked content files. Sound6
reports36864 backing codes but retains its30912-code logical window; all raw tail/page
bytes are preserved separately from the preview (sound6-nine-page-results.md).
The pending one-page ordinary-WAV import has no hardware recapture yet. Project JSON
remains read-only and public operation contexts are unchanged.

The one-page WAV import is now hardware-accepted with exact retained capacity and
endpoint. The current export is
**experiments/exported-one-page-sound6-import-001/project.json**, with seven melodic/
three calibrated drum previews and32 checked content files. Sound6's4096-code backing
has a2344-code logical window and4801-frame48k preview; all raw/source records remain
exact (sound6-one-page-import-results.md). The new import command writes a separate
restore package, not this read-only JSON. The mono44.1k candidate is pending hardware
testing; export schema/version remain unchanged.

Reproduce in a fresh folder:

```powershell
.\.venv\Scripts\python.exe -m po33_re export-project experiments/edited-sound2-remove-001/derived/analysis-001/capture.symbols.npz --capture experiments/edited-sound2-remove-001/capture.wav --out-dir experiments/exported-project-002
```

## Export after the accepted mono WAV import

The current genuine capture exports to
`experiments/exported-mono-WAV-sound6-import-001/project.json`. Seven melodic previews,
three calibrated drum previews, all 32 content hashes and the entire reconstructed
raw native body pass. Sound6 now previews the imported rising sweep; Sound7 remains
empty. The project stays read-only. The next copy candidate is separate from this
accepted export (sound6-mono-WAV-import-results.md; imported-sound6-to7-copy-control.md).

## Export after copying the imported sample

The current genuine export is
`experiments/exported-imported-sound6-to7-copy-001/project.json`. All eight melodic slots
and three calibrated drum slices preview successfully; all 33 content hashes and the
complete raw native body match. Sound6/Sound7 preview WAVs are identical. The export
remains read-only and does not include the pending deletion prediction
(imported-sound6-to7-copy-results.md).

## Export after imported shared deletion

The genuine transferred state exports to
`experiments/exported-imported-shared-sound6-deletion-001/project.json`. Sound6 is empty;
Sound7 owns and previews the same imported sweep. Seven melodic and three calibrated
drum previews, all 32 content hashes and the full native body pass. The export remains
read-only, separate from the pending final-owner deletion prediction
(imported-shared-sound6-deletion-results.md).

## Export after completing the imported lifecycle

`experiments/exported-imported-last-owner-deletion-001/project.json` is the current
genuine read-only export: Sound6/7 empty, six melodic previews and three calibrated
drum previews. All 31 content hashes and the complete reconstructed native body pass.
The body also equals the independent earlier empty-slot capture. Tempo remains an
opaque uneditable field while the first controlled observation is pending
(imported-unshared-sound7-deletion-results.md; tempo-preset-control.md).

## Export after the observed140 BPM preset

`experiments/exported-tempo-140-001/project.json` is the current genuine read-only export.
Six melodic and three calibrated drum previews, all31 content hashes and the complete
native body pass. All sample/pattern content is unchanged from the120 baseline. The
single changed opaque global byte is preserved literally; no editable tempo property
is exposed from this first association (tempo-120-to140-results.md).

## Exports after the third tempo preset and original return

The80 state exports to `experiments/exported-tempo-80-001/project.json`; the current120
return exports to `experiments/exported-tempo-return120-001/project.json`. Both preserve
six melodic and three calibrated drum previews, all31 content hashes and their full
native bodies. Sample/pattern content is unchanged, and the120 raw body also equals
the independent original. Tempo remains an opaque read-only byte pending the generated
restore gate (tempo-preset-series-results.md; generated-tempo80-control.md).

## Export after the accepted generated 80 BPM edit

`experiments/exported-generated-tempo80-001/project.json` is the current genuine read-only
export. Six melodic and three calibrated drum previews, all 31 content hashes and full
native-body reconstruction pass. Samples and patterns remain exact; the tempo byte is
preserved literally in source packets. Preset editing uses separate hash-bound plans,
and the pending fine-tempo control does not make project JSON writable
(generated-tempo80-results.md; tempo-preset-edits.md).

## Export after the physical fine100 control

`experiments/exported-fine-tempo100-001/project.json` is the current genuine read-only
export. Six melodic and three calibrated drum previews, all31 content hashes and the
complete native body pass. Only the literal tempo byte differs from the accepted80
state; all sound parameters/sample/pattern content is unchanged. Public preset editing
rejects this100 source until suitable fine-tempo evidence supports an extension
(fine-tempo100-results.md; fine-tempo-range-series-control.md).

## Exports after fine-tempo limits and exact return

The60/240 states export to `experiments/exported-fine-tempo60-001/project.json` and
`experiments/exported-fine-tempo240-001/project.json`. The current100 return is
`experiments/exported-fine-tempo-return100-001/project.json`. Each has six melodic and
three calibrated drum previews, all31 content hashes and complete native-body checks
passing. All non-tempo content is unchanged; the return also matches the independently
original100 body. Project JSON remains read-only, with fine writing still pending
(fine-tempo-range-series-results.md; generated-fine-tempo137-control.md).

## Export after the accepted137 restore

`experiments/exported-generated-fine137-001/project.json` is the current genuine read-only
export. Six melodic and three calibrated drum previews, all31 content hashes and full
native-body reconstruction pass. All non-tempo content is exact. Tempo editing uses
separate hash-bound plans; project JSON remains read-only while swing investigation
begins (generated-fine-tempo137-results.md; tempo-edits.md; swing-max-control.md).

## Export after the physical maximum swingS18

`experiments/exported-swing-max18-001/project.json` is the current genuine read-only
export. Six melodic and three calibrated drum previews, all31 content hashes and
complete native-body reconstruction pass. Samples/patterns remain exact, with only
the adjacent literal swing byte changed and tempo137 preserved. Existing tempo edits
reject this new opaque swing context pending suitable evidence
(swing-max18-results.md; swing-range-series-control.md).

## Export after the complete physical swing range

`experiments/exported-swing-range-return18-001/project.json` is the current genuine
read-only export. All 31 content hashes, six melodic previews, three calibrated drum
previews and complete native-body reconstruction pass. The returned body exactly
matches the earlier S18 state; samples and patterns are unchanged. Project views retain
the literal swing byte. Separate research WAVs add a controlled offbeat note for the
next timing test; project JSON remains read-only (swing-range-results.md;
swing-timing-pair-control.md).

## Export after generated straight offbeat restore

`experiments/exported-swing-timing0-001/project.json` is the current genuine read-only
export. All 31 content hashes and the complete native body match the exact accepted
straight target. Samples are preserved; Pattern 1 gains only the cloned Step 2 event,
and tempo/swing bytes are 137/0. Separate ordinary playback supplies the measured
straight reference; it is not imported as sample data or interpreted as backup audio
(swing-straight-control-results.md; swing-timing-pair-control.md).

## Export after generated positive swing verification

`experiments/exported-swing-timing6-001/project.json` is the current genuine read-only
export. All 31 content hashes, calibrated previews and complete native-body recovery
pass. Its samples and pattern bytes match the straight control; tempo/swing bytes are
137/6. Ordinary audio verifies the positive offbeat timing separately. Compiler plans
provide bounded swing edits while project JSON remains read-only
(generated-swing6-results.md; swing-edits.md).

## Export after joint tempo100/swing9 acceptance

`experiments/exported-joint-tempo100-swing9-001/project.json` is the current genuine
read-only export. All 31 content hashes, calibrated previews and complete native-body
reconstruction pass. Samples and patterns match the earlier swing-6 state; only the
two calibrated global fields change to100/9. Live sound volume remains unmodeled and
will be investigated using fresh selection and minimum-volume captures
(joint-tempo-swing-results.md; sound3-volume-probe-control.md).

## Export after stopped live-volume probe

`experiments/exported-sound3-live-volume-minimum-001/project.json` is the current genuine
read-only export. Its complete native body is unchanged from joint100/swing9, and all
31 content hashes and preview validations pass. The previews retain the raw unchanged
sample codes and cannot reproduce the quieter live gain reported after the stopped
knob action. No persistent volume field has been observed in those snapshots;
recorded TONE parameters remain a separate investigation
(sound3-live-volume-results.md; sound3-tone-lock-probe-control.md).

## Export after recorded Sound3 TONE maximum

`experiments/exported-sound3-tone-lock-maximum-001/project.json` is the current genuine
read-only export. All31 content hashes and complete native-body reconstruction pass.
Samples/global bytes remain exact. Pattern1 retains all16 raw Sound3 primary cells
changed by the TONE pass, including formerly empty cells; no new-note interpretation
is imposed. Sample previews retain raw sample data and do not render the pattern's
gain changes. Volume-specific mapping remains under investigation
(sound3-tone-lock-up-results.md; sound3-volume-lock-range-control.md).

## Export after the exact volume maximum return

`experiments/exported-sound3-volume-range-return-maximum-001/project.json` is the current
genuine read-only export. Its full body exactly matches the prior recorded maximum;
all31 content hashes and native reconstruction pass. The failed narrow minimum model
is preserved in separate reports and does not alter exported raw data. A broader
six-bit/enable alternative remains under investigation, with no gain-rendered preview
or public volume writer (sound3-volume-lock-range-results.md;
sound3-volume-middle-series-control.md).

## Export after the interior series maximum return

`experiments/exported-sound3-volume-middle-return-maximum-001/project.json` is the current
genuine read-only export. All31 content hashes and full native-body reconstruction pass.
The maximum body exactly matches prior physical endpoints; the separate middle capture
retains its nonuniform raw parameters. Neither export averages values or renders a gain
curve. Reference21/candidate18 research WAVs are separate source-bound artifacts pending
hardware/audio evidence (sound3-volume-middle-series-results.md;
generated-sound3-volume18-control.md).

## Export after the uniform21 reference replay

`experiments/exported-sound3-volume21-reference-001/project.json` is the current genuine
read-only export. Its complete body matches the independent recorded quarter source
and the reference restore target. All31 content hashes and reconstruction checks pass.
Separate ordinary playback is usable under the frozen gain method; raw sample previews
do not render those pattern parameters. Generated18 remains pending physical reception
and audio comparison (generated-sound3-volume18-control.md).

## Export after the accepted generated18 restore

`experiments/exported-sound3-volume18-001/project.json` is the current genuine read-only
export. Its complete body matches the generated18 target and physical recapture.
All31 content hashes and reconstruction checks pass. Samples, keys and globals100/9
remain unchanged; the new pattern fields are retained literally. Separate tone audio
shows lower amplitude under the frozen comparison, but sample previews do not render
pattern gain. No gain curve or public volume writer is inferred
(generated-sound3-volume18-results.md; generated-sound3-volume36-control.md).

## Export after the accepted generated36 restore

`experiments/exported-sound3-volume36-001/project.json` is the current genuine read-only
export. Its complete body matches the fixed36 target and physical recapture, and
all 31 content hashes/reconstruction checks pass. Samples and keys remain unchanged.
The uniform raw pattern volume is retained literally; sample previews do not render
pattern gain. The bounded volume edit plan is separate from this read-only view
(generated-sound3-volume36-results.md; sound3-volume-edits.md).

## Export after exact post-playback persistence

`experiments/exported-sound3-volume36-post-playback-001/project.json` is the current
genuine read-only export. All 31 content hashes and native reconstruction checks pass.
Its complete body and packets match the accepted volume 36 restore before ordinary
playback. No sample data or note changes occur. The next recorded TONE A probe uses
this actual unchanged baseline; raw previews do not render pattern parameters
(sound3-volume-post-playback-results.md; sound3-tone-pitch-probe-control.md).

## Export after the recorded pitch minimum

`experiments/exported-sound3-tone-pitch-minimum-001/project.json` is the current genuine
read-only export. All 31 content hashes and full native reconstruction pass. Pattern
data retains raw candidate 1 and volume 36 literally. Sample codes, keys and all other
state remain unchanged; sample previews do not render the pitch shift. The prior
bounded volume editor rejects this changed nonvolume context, and project JSON remains
a read-only view (sound3-tone-pitch-minimum-results.md; sound3-tone-pitch-range-control.md).

## Export after the exact pitch minimum return

`experiments/exported-sound3-tone-pitch-return-minimum-001/project.json` is the current
genuine read-only export. All 31 content hashes and full native reconstruction pass.
The complete body exactly equals the independent earlier pitch minimum, with raw
candidate 1 and volume 36. Samples and keys remain exact; raw previews do not render
the pitch shift. Generated 13/14 research controls are separate artifacts pending
physical reception and ordinary audio (sound3-tone-pitch-range-results.md;
generated-sound3-pitch-pair-control.md).

## Export after the accepted generated pitch13 reference

`experiments/exported-sound3-pitch13-reference-001/project.json` is the current genuine
read-only export. Its complete body matches the generated13 target and physical
recapture, including parameter-only cells now carrying13. All31 content hashes and
native reconstruction checks pass. Ordinary playback is usable under the unchanged
frozen frequency method. Raw sample previews retain unchanged codes and do not render
pattern pitch; candidate14 and its interval hypothesis remain pending
(generated-sound3-pitch-pair-control.md).

## Export after accepted generated pitch14 and measured interval

`experiments/exported-sound3-pitch14-001/project.json` is the current genuine read-only
export. All31 content hashes and native reconstruction pass. Its complete body matches
the generated14 target and physical recapture, with volume36, sample data and keys
unchanged. Separate ordinary audio supports the roughly one-semitone13→14 interval;
raw previews do not render it. Public raw pitch plans are separate from this view
(generated-sound3-pitch-interval-results.md; sound3-pitch-edits.md).

## Export after unchanged FILTER selection

`experiments/exported-sound3-filter-selection-001/project.json` is the current genuine
read-only export. All31 content hashes and complete native reconstruction pass.
Its full body equals the accepted generated14 body, with pitch14, volume36, samples
and keys unchanged. Mode selection and prior ordinary playback produce no stored
change in this control. Recorded FILTER A remains pending against this actual
baseline; no filter-rendered preview or decoded cutoff value is claimed
(sound3-filter-probe-control.md).

## Export after recorded FILTER A clockwise

`experiments/exported-sound3-filter-A-clockwise-001/project.json` is the current genuine
read-only export. All31 content hashes and full native reconstruction pass. Raw
pattern data retains the candidate projection62, with pitch14, volume36, samples and
keys unchanged. Sample previews do not render the high-pass effect reported by the
user. Other third-byte bits remain opaque and no filter scale/writer is inferred
(sound3-filter-A-clockwise-results.md; sound3-filter-A-range-control.md).

## Export after the exact FILTER clockwise return

`experiments/exported-sound3-filter-A-return-clockwise-001/project.json` is the current
genuine read-only export. All 31 content hashes and complete native reconstruction
pass. Its full body matches the independent earlier clockwise backup, with contiguous
62 / alternate 59, pitch 14, volume 36, sample codes and keys unchanged. Raw sample
previews do not render the reported filter effect. Center native and ordinary-audio
checks remain pending; no filter-rendered preview or public filter writer is enabled
(sound3-filter-A-range-results.md; sound3-filter-A-center-control.md).

## Export after the audible FILTER center

`experiments/exported-sound3-filter-A-center-001/project.json` is the current genuine
read-only export. All 31 content hashes and complete native reconstruction pass.
Its body carries literal 63 under both candidate projections, with pitch 14, volume
36, samples and keys unchanged. Native validity does not rescue the failed
between-endpoint scalar hypotheses. Separate ordinary audio supports the repeated
component's near-prior amplitude; broadband bypass is unconfirmed. Previews retain
raw sample codes and do not render recorded filter or pitch effects. New interior
captures and exact complete center return remain pending
(sound3-filter-A-center-results.md; sound3-filter-A-interior-control.md).

## Export after the exact FILTER interior center return

`experiments/exported-sound3-filter-A-interior-center-return-001/project.json` is
the current genuine read-only export. All 31 content hashes and full native
reconstruction pass. Its entire body matches the independently observed center63,
with pitch 14, volume 36, samples and keys exact after recorded LPF16 and HPF52.
User listening and branch-order results are separate from raw previews, which do
not render filter effects. Generated research WAVs are separate artifacts with
hardware acceptance pending; no general filter writer or rendered preview is
enabled (sound3-filter-A-interior-results.md; generated-sound3-filter-pair-control.md).

## Export after accepted generated FILTER16

`experiments/exported-sound3-generated-filter16-001/project.json` is the current
genuine read-only export. All 31 content hashes and complete native reconstruction
pass. Its full body matches the generated16 target and independently recorded LPF
body, retaining pitch 14, volume 36, sample codes and keys. Raw previews do not
render user-confirmed filtering. The generated high-pass52 acceptance remains
pending and no public filter writer is enabled
(generated-sound3-filter16-results.md; generated-sound3-filter-pair-control.md).

## Export after accepted generated FILTER52

`experiments/exported-sound3-generated-filter52-001/project.json` is the current
genuine read-only export. All31 hashes and full native reconstruction pass. Its
entire body matches generated52 and independent recorded HPF, with pitch14,
volume36, sample codes and keys exact. Raw previews do not render filtering. Public
observed-code plans remain separate from this view; the generated63 center return
is prepared with hardware acceptance pending
(generated-sound3-filter-pair-results.md; sound3-filter-edits.md;
generated-sound3-filter-center-control.md).

## Export after accepted public FILTER63 center

`experiments/exported-sound3-generated-filter63-001/project.json` is the current
genuine read-only export. All31 hashes and complete native reconstruction pass.
Its entire body equals the independently recorded center63, preserving pitch14,
volume36, sample codes and keys after generated52. User-confirmed unfiltered
playback remains separate from raw previews. The next B probe has no guessed
resonance endpoint or rendered response, and existing public guards stay unchanged
(generated-sound3-filter63-results.md; sound3-filter-B-probe-control.md).

## Export after recorded B minimum

`experiments/exported-sound3-filter-B-minimum-001/project.json` is the current genuine
read-only export. All31 hashes and full native reconstruction pass. Its body has
third-primary bits2..7 cleared in all16 Sound3 cells, preserving pitch14/volume36,
cutoff63, samples and keys. The user reports no audible change; raw previews do
not render resonance. Existing public cutoff guards intentionally reject this new
third-byte layout and remain unchanged; new B maximum and exact return are pending
(sound3-filter-B-minimum-results.md; sound3-filter-B-range-control.md).

## Export after exact B minimum return

`experiments/exported-sound3-filter-B-return-minimum-001/project.json` is the current
genuine read-only export. All31 hashes and complete native reconstruction pass.
Its entire body matches the independent B0 minimum, with cutoff63, pitch14,
volume36, samples and keys exact after the B63 pass. Raw previews do not render
resonance. The new generated LPF16/B0-B63 pair is separate and hardware-unverified;
public cutoff guards remain unchanged
(sound3-filter-B-range-results.md; generated-sound3-resonance-pair-control.md).

## Export after accepted LPF16/B0 reference

`experiments/exported-sound3-filter16-B0-reference-001/project.json` is the current
genuine read-only export. All31 content hashes and full native reconstruction pass.
Its entire body equals the generated combined reference, with cutoff16/B0 and
pitch14/volume36, sample codes and keys preserved. Separate frozen ordinary audio
is usable for the next comparison. Raw previews do not render the filter, and
generated B63 reception plus amplitude evidence remain pending
(generated-sound3-resonance-reference-results.md; generated-sound3-resonance-pair-control.md).

## Export after accepted LPF16/B63 candidate

`experiments/exported-sound3-filter16-B63-candidate-001/project.json` is the current
genuine read-only export. All31 hashes and complete native reconstruction pass.
Its entire body equals the generated candidate, with cutoff16 and pitch14/volume36,
samples and keys exact relative to the B0 reference. Separate frozen audio supports
the component-amplitude increase; raw previews do not render it. A generated B32
interior target remains separate and hardware-unverified
(generated-sound3-resonance-pair-results.md; generated-sound3-resonance-middle-control.md).

## Export after accepted LPF16/B32 middle

`experiments/exported-sound3-filter16-B32-middle-001/project.json` is the current
genuine read-only export. All31 hashes and full native reconstruction pass. Its
entire body equals the generated middle, preserving cutoff16/pitch14/volume36,
samples and keys relative to B63. Frozen audio supports the between-endpoint
component bounds; previews do not render the effect. Public resonance plans remain
separate and guarded. The next FX location probe is registered with no raw target
prediction (generated-sound3-resonance-middle-results.md; sound3-resonance-edits.md;
pattern1-FX-probe-control.md).

## Export after recorded FX7

`experiments/exported-pattern1-FX7-recorded-001/project.json` is the current genuine
read-only export. All31 content hashes and full native reconstruction pass. It
preserves literal footer66 and global byte131=9 alongside unchanged samples,
keys and sound parameters. This does not rescue the failed footer-only model.
User-confirmed octave-up remains separate from raw previews, which do not render
effects. The next FX8/clear controls retain the unknown global role and both nibble
orders (pattern1-FX7-results.md; pattern1-FX8-clear-control.md).

## Export after recorded FX8

`experiments/exported-pattern1-FX8-recorded-001/project.json` is the current genuine
read-only export. All31 hashes and complete native reconstruction pass. Literal
footer77/global1 are preserved with unchanged samples, keys and sound parameters.
User-confirmed lower octave is separate from raw previews. No clear export is
claimed because that supplied WAV duplicates the FX8 recording; corrected clear
input remains pending (pattern1-FX8-results.md; pattern1-FX16-corrected-clear-control.md).

## Export after corrected FX16 clear

`experiments/exported-pattern1-FX16-corrected-clear-001/project.json` is now the
current genuine read-only export. All31 hashes and full native reconstruction
pass. It preserves footerFF and global131=7. Every other state byte equals the
independent original no-FX baseline; entire baseline-body equality is false.
The earlier normal listening report remains separate from raw previews. No
global meaning, nibble order or public FX writer is inferred
(pattern1-FX16-corrected-clear-control.md; pattern1-playback-global-control.md).

## Export after ordinary playback and reported battery replacement

`experiments/exported-pattern1-plain-playback-001/project.json` is now the current
genuine read-only export. All31 hashes and complete native reconstruction pass;
its entire body equals the accepted pre-battery-change clear state, including
footerFF/global7. Two distinct raw recordings support the unchanged state.
The generated footer6/global7 target is separate and remains hardware-unverified.
Raw sample previews do not render the saved octave effect
(pattern1-plain-playback-results.md; generated-pattern1-FX-up-control.md).

## Export after accepted generated footer6/global7

`experiments/exported-pattern1-generated-FX6-global7-up-001/project.json` is now
the current genuine read-only export. All31 hashes and full native reconstruction
pass. Footer66 and global131=7 are literal; the user reports an audible octave
effect in the requested up-test context. All samples, notes and parameters remain
exact, and raw previews do not render the saved effect. New generated down/clear
targets remain separate from this physical export
(generated-pattern1-FX-up-results.md; generated-pattern1-FX-return-control.md).

## Export after exact generated clear/global7 return

`experiments/exported-pattern1-generated-FX15-global7-clear-001/project.json` is
now the current genuine read-only export. Both down and clear exports have all31
hashes and full native reconstruction checked. The final body exactly equals
the independent clear/global7 baseline, and the user confirms normal playback.
Uniform effect editing is available through separate guarded plans; the exported
project JSON remains read-only. Mixed effects remain research-only and previews
continue to omit sequencer effects
(generated-pattern1-FX-return-results.md; pattern1-effect-edits.md;
generated-pattern1-FX-mixed-control.md).

## Export after accepted mixed effect halves

`experiments/exported-pattern1-FX6-7-halves-global7-001/project.json` is now the
current genuine read-only export. All31 hashes and full native reconstruction
pass. Literal footer6666666677777777 and global7 accompany unchanged notes,
samples and parameters. User-confirmed higher then lower playback remains
separate from raw previews. Complementary first-pair targets are research-only
(generated-pattern1-FX-mixed-results.md; pattern1-FX-first-pair-control.md).
