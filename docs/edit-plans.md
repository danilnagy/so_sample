# Compile guarded JSON edit plans

> This document grew as an append-only log: a test described as pending in one paragraph
> is usually settled in a later one or in its results document. Current status: every plan
> operation listed here has been verified on the device unless its section says otherwise;
> see the [format reference](format-reference.md) for the settled facts.

`apply-edits` turns a readable plan into a restore WAV using only the existing bounded
writers. The plan binds both the exact source artifact and its native body hash. Stale
source hashes, unknown operations, extra/missing arguments and unsupported contexts
are rejected before output is created. The output folder must be fresh.

The executable replay plan is **experiments/replay-window-edit-001/plan.json**:

```json
{
  "schema": "po33.edit-plan",
  "schema_version": 1,
  "source_artifact_sha256": "3b6eb02794d58a4a08094dd53ace16147a03e5f61696adbf72864d2dc2d79b90",
  "source_body_sha256": "002346273de5b027d53b593e8183b3695ba680bcd01543286def0bc68d24f696",
  "operations": [
    {"operation": "set_sound_end", "sound": 3, "end": 39393}
  ]
}
```

Use the original minimum artifact for this particular plan; the now-edited recapture
has different source hashes and is intentionally rejected by the same plan.

| Operation | Arguments and current scope |
| --- | --- |
| `set_parameter_locks` | as `set_step_parameters`, but a step without a note gets a parameter-only cell (primary bytes, zero auxiliary byte), the layout the device writes for a lock on an empty step. [Hardware verified](param-only-results.md) for filter: the lock holds for later unlocked notes |
| `set_sample_window` | `sound` (melodic 1..8 owning its buffer), `start`, `end` (codes, 0 <= start < end <= capacity); rewrites the record's start and end fields. [Hardware verified](sample-window-results.md): the note plays from start to end |
| `set_step_parameters` | `pattern`, `sound`, `parameter` (`pitch` 1..25, `volume`, `filter`, `resonance` 0..63), `values`; 16 entries, `null` keeps a step. Only steps with a note can be written; every other bit, including unknown bit 5, is kept. The bit layout matches all four calibrated field modules ([codec](../src/po33_re/formats/notes.py)); per-step pitch is [hardware verified](pitch-law-results.md) at one semitone per code |
| `copy_pattern` | `source_pattern`, `destination_pattern` (1..16, different); copies every byte of the pattern, including the effects footer. [Hardware verified](selected-pattern-results.md) on Pattern 1 to Pattern 5 |
| `set_pattern_chain` | `patterns`: a list of 1..128 patterns, each 1..16; writes the entries to second global record bytes 0.. and the length to byte 128. Layout [observed](pattern-chain-results.md); writer [hardware verified](chain-writer-results.md) |
| `set_swing_byte` | `value` (0..18); writes byte 130 of the second global record without the opaque-context guard of `set_swing`. Timing [measured](swing-law-results.md): even steps are delayed by value/24 of a step |
| `set_selected_pattern` | `pattern` (1..16); writes a chain of one: byte 0 of the second global record as pattern - 1 and length 1. [Hardware verified](selected-pattern-results.md): the device plays the selected pattern after a restore |
| `set_drum_notes` | `pattern`, `sound` (drum 9..16), `keys`, `template_sound` (1..16); 16 entries, step 1 first, each `null` or a key 1..16 written as auxiliary byte 0x10 + key - 1. Notes copy the parameters of the template sound's notes in the pattern. All 16 keys are [hardware verified](drum-notes-writer-results.md) on Sound11: key k plays the kit's k-th window |
| `set_melodic_notes_from` | `pattern`, `sound`, `keys`, `template_sound`; as `set_melodic_notes`, but new notes copy the parameters of another melodic sound's notes in the pattern, so a sound with no notes yet can be written |
| `set_notes` | `pattern`, `sound` (1..16), `keys`, `parameters` {pitch, volume, filter, resonance}; writes notes with explicit parameters, melodic or drum auxiliary byte by sound range, no template needed. [Hardware verified](project-build-results.md) |
| `set_tempo_byte` | `bpm` (60..240); writes byte 129 of the second global record without the opaque-context guard of `set_tempo`. [Hardware verified](project-build-results.md) at 100 BPM |
| `set_melodic_notes` | `pattern`, `sound` (melodic 1..8), `keys`; 16 entries, step 1 first, each `null` or a key 1..16. Notes copy the parameters of that sound's existing notes in the pattern, which must be identical; `null` clears the cell. Key layout is [hardware-confirmed](pattern1-key-scale-map-results.md) on Sound 3; the writer is [hardware verified](melodic-notes-writer-results.md) through this plan path |
| `set_step_effects` | `pattern`, `effects`; 16 entries, step 1 first, each `null` or an FX key 1..15; changes only that pattern's eight footer bytes. Layout and codes are hardware-confirmed ([layout](pattern1-FX-position-map-results.md), [codes](FX-code-map-results.md)); the writer is [hardware verified](step-effects-writer-results.md) through this plan path |
| `set_pattern1_effect` | `effect`; uniform `none`, `octave_up`, `octave_down`, exact calibrated global7 project only; all other state pinned and mixed effects rejected; see [scope](pattern1-effect-edits.md) |
| `set_sound3_resonance` | `value`; only observed integer codes0/32/63, all16 Sound3/Pattern1 cells at fixed cutoff16/pitch14/volume36, uniform tested or legacy note32/parameter0 source; see [scope](sound3-resonance-edits.md) |
| `set_sound3_filter` | `value`; only observed integer raw codes1/16/52/62/63, all16 Sound3/Pattern1 cells in the tested pitch14/volume36 layout; see [scope and evidence](sound3-filter-edits.md) |
| `delete_melodic_sound` | `sound`; only the observed shared Sound6-to-Sound7 full-buffer transfer, or unshared self-owned Sound7 removal with Sound6 empty;32768 codes/window0/30912 and no Sound6/7 pattern events |
| `copy_melodic_reference` | `source_sound`, `destination_sound`; only unshared self-owned Sound6/32768 codes/header0/30912/owner5 into existing empty Sound7, adding its exact nine-byte reference |
| `clone_drum_cell` | `pattern`, `sound`, `source_step`, `target_steps`; Pattern1/Sound10 observed raw0df883/10 cell into empty targets, accepted nonzero copied sample and calibrated Sound2/Sound3 neighbors |
| `remove_drum_cell` | `pattern`, `sound`, `steps`; clear occupied observed Pattern1/Sound10 cells under the same sample/neighbor guards |
| `copy_drum_slice` | `source_sound`, `source_slice`, `destination_sound`, `destination_slice`; existing Sound9/keys1 or2 to Sound10/key1, owner0, calibrated source windows and literal neighboring references; the exact key2 transfer now has separate hardware evidence |
| `set_drum_slice_end` | `sound`, `slice`, `end`; Sound9/key1 start0/end127..4044 or key2 start4045/end4172..8088, owner0 and literal other14 references |
| `set_sound_end` | `sound`, `end`; Sound3 at either observed start, retaining its local endpoint bounds |
| `set_sound_window` | `sound`, `start`, `end`; explicit Sound3 window at start11716 or31393, within that start's local endpoint interval |
| `set_note_key` | `pattern`, `step`, `sound`, `key`; calibrated single Sound 3 cells and keys1/2/7/16 |
| `clone_sound_cell` | `pattern`, `sound`, `source_step`, `target_steps`; observed Sound 2 cell and supported neighbours |
| `remove_sound_cell` | `pattern`, `sound`, `steps`; occupied observed Sound 2 cells and supported neighbours |
| `clone_step` | `pattern`, `source_step`, `target_steps`; prior opaque single-event source and empty target rows |

Operations are applied in order, with every intermediate frame strictly decoded. Each
library operation retains its calibration and context guards. Unknown packets and fields
are preserved. The compiler rebuilds verified packets with an explicit carrier ending,
encodes a 44.1 kHz PCM16 WAV and requires a full phase/count and exact native-body roundtrip.
It records source/plan hashes and a before/after body trace for each operation.

Output contains `plan.json`, `edited.symbols.npz`, `restore.wav`, `redecoded.symbols.npz`
and `compile-report.json`. Reports always retain `hardware_verified: false`; producing
audio is not a new hardware restore. Arbitrary raw packet or view-JSON edits, sample
allocation and unknown fields are not supported by this interface.

The replay at **experiments/compiled-verified-window-001/restore.wav** equals the accepted
restore file byte for byte, SHA-256
`06b311337489a1176c80bc27172b343dc649ec2bd4c6880ad0d967470527949f`.
Its complete body equals the genuine recapture. See
[replay audit](../experiments/edit-plan-replay-validation-001.json) and
[hardware result](native-nonzero-trim-results.md). Other combinations require appropriate
evidence; no broad hardware claim is inferred from this replay.

Reproduce in a fresh folder:

```powershell
.\.venv\Scripts\python.exe -m po33_re apply-edits experiments/event-013-b-sound3-start-min/derived/analysis-001/capture.symbols.npz --plan experiments/replay-window-edit-001/plan.json --out-dir experiments/compiled-verified-window-002
```

For future work, use the source artifact copied into a project export and create a plan
bound to its own recorded hashes. The read-only views remain observations; the separate
plan is the writable interface. A graphical editor is still future work.

The second-start replay plan at **experiments/replay-two-start-window-001/plan.json**
uses `set_sound_window` to move31393/39393 to11716/19716. Its compiled restore equals
the second hardware-accepted WAV byte for byte. The inverse reproduces the first
hardware body's complete native packets. See
[two-start results and exact local bounds](native-quarter-window-results.md). Interpolated
start values and arbitrary windows remain rejected; this replay is not a new hardware test.

The first drum plan is **experiments/drum9-slice-end-plan-001/plan.json**, bound to the
genuine Sound9/key1 minimum artifact. It sets only that slice's endpoint to2000. Both
genuine minimum/copy bodies and inverses are reproduced by the bounded writer; compiler
roundtrips pass, but this new operation awaits its
[first hardware restore test](native-drum9-slice-end-restore-test.md). The failed exact79
prediction is retained, and other slices/contexts remain unsupported.

That first `set_drum_slice_end` plan now has separate matching hardware evidence:
the full recapture equals its registered target, and the user confirms both tone checks.
See [drum hardware results](native-drum9-slice-end-results.md). Compiler reports remain
software-only. Scope remains Sound9/key1 at zero start with the original other15 records;
the [next physical key2 control](drum9-key2-trim-min-control.md) does not broaden it in advance.

The key2 control now passes the exact endpoint hypothesis and its reported click supports
a local nonzero-start interpretation. Both controlled slices may vary inside their own
guards while the remaining14 references stay literal. The first key2 plan is
**experiments/drum9-key2-end-plan-001/plan.json**, setting endpoint6045 while preserving
key1 endpoint2000. It passes software compilation and awaits its
[separate hardware test](native-drum9-key2-end-restore-test.md). This does not imply
that arbitrary two-operation combinations have already been restored.

That key2 plan now has its own exact matching clean hardware recapture and user-confirmed
tones, preserving the accepted key1 window. See
[nonzero-start drum hardware results](native-drum9-key2-end-results.md). Source hashes,
local bounds and the literal remaining14 references still constrain every plan. The next
[Sound10 copy control](drum10-copy-control.md) tests another block without broadening
Sound10 editing in advance; compiler reports remain software-only.

The physical cross-drum key1 copy now confirms the destination key1 mapping and exact
reference transfer. The writer reproduces both whole genuine control bodies and an
inverse through bounded source edits. The next plan is
**experiments/drum-slice-copy-plan-001/plan.json**, copying Sound9/key2's nonzero-start
reference into existing Sound10/key1. It has strict waveform/body checks but awaits
its [own hardware test](native-cross-drum-slice-copy-restore-test.md). It retains all
source records and allocates no sample data. Arbitrary drum keys/slots and destination
endpoint editing are unsupported.

The generated key2 transfer now has an exact full-target recapture with543 valid
checksums and user-confirmed restore/tone checks. See
[cross-drum hardware results](native-cross-drum-slice-copy-results.md). The original
compiler/software reports remain `hardware_verified: false`; acceptance is separate.
Existing mapping/context guards are retained, and no drum pattern writer is introduced.

The physical Sound10/key1 note now passes preservation/cell mapping checks. Its actual
auxiliary10 differs from the failed melodicF0 prediction. New drum-cell operations copy
or clear the observed opaque0df883/10 pair, retaining Pattern1, the accepted nonzero
copied window and calibrated neighboring Sound2/Sound3 notes. Unknown/occupied contexts
are rejected. The first plan is **experiments/drum-cell-copy-plan-001/plan.json**, adding
the Step1 note at Step9. Whole genuine bodies/inverses and waveform checks pass, but its
[generated hardware test](native-drum-cell-copy-restore-test.md) was pending at the time (accepted since; see below). No drum-key
setter or general parameter interpretation is introduced.

The first `clone_drum_cell` plan now has an exact matching device recapture and user-
confirmed grids/playback, with source and melodic notes intact. See
[hardware results](native-drum-cell-copy-results.md). Writer guards remain unchanged,
and compiler/software reports remain unverified by hardware themselves. The
[next physical key2 control](drum10-step9-key2-control.md) compares its unknown key value
without enabling key2 editing or a general auxiliary-byte interpretation in advance.

The hardware-validated melodic reference copy is now available as
`{"operation":"copy_melodic_reference","source_sound":6,"destination_sound":7}`.
Its source must be the observed zero-start32768-code Sound6 layout, with no other
referrers to owner5; Sound7 must be empty, with no dangling references to its own
selector. Other sound pairs, bool values, wrong layouts and occupied/shared contexts
are rejected. All samples, patterns and unknown packets outside the new reference
are preserved. Source4-to5 remains a research reconstruction, outside this public scope.

The plan **experiments/replay-sound6-to7-copy-001/plan.json**, compiled into
**experiments/compiled-sound6-to7-copy-001/restore.wav**, reproduces the earlier accepted
copy's entire body and restore WAV byte-for-byte. This is a software replay of the
already tested WAV, with its compiler report remaining `hardware_verified:false`.
See [copy hardware results](sound6-to7-generated-copy-results.md). The plan binds the
earlier created-Sound6 artifact; the current post-deletion backup has different hashes
and an occupied Sound7, and is intentionally rejected by that same plan.

```powershell
.\.venv\Scripts\python.exe -m po33_re apply-edits experiments/edited-sound6-create-001/derived/analysis-001/capture.symbols.npz --plan experiments/replay-sound6-to7-copy-001/plan.json --out-dir experiments/compiled-sound6-to7-copy-002
```

The physical shared-owner deletion now has exact serialized transfer evidence,
but generated deletion and general allocation are still outside this edit-plan interface.

Both observed deletion contexts are now available through
`{"operation":"delete_melodic_sound","sound":6}` or `"sound":7`. Sound6 must own the
observed32768-code0/30912 buffer and have only the exact Sound7 reference; the operation
transfers all codes and original packet geometry to self-owner6 under Sound7, clearing
Sound6. Sound7 deletion requires that observed self-owned buffer, no other referrers
and an empty Sound6. Unsupported slots, window/layout changes, additional referrers
and any Sound6/7 pattern events are rejected. The operations preserve every unrelated
packet, pattern and tail code. They do not infer policies for arbitrary deletion contexts.

The composed plan **experiments/replay-melodic-copy-delete-cycle-001/plan.json** copies
Sound6 to7, deletes shared Sound6, then deletes unshared Sound7. Each intermediate
body equals its corresponding genuine hardware capture; its final compiled WAV at
**experiments/compiled-melodic-copy-delete-cycle-001/restore.wav** equals the earlier
hardware-accepted Sound4 shrink restore byte-for-byte, SHA-256
`9fb25b37196de46a708a67b087fce34b931cba9f3067e86862b3cc9eab656fbb`.
The new compiler report remains `hardware_verified:false`; no additional device restore
is claimed for this software replay. See [shared deletion](shared-sound6-deletion-results.md)
and [last-owner deletion](unshared-sound7-deletion-results.md).

```powershell
.\.venv\Scripts\python.exe -m po33_re apply-edits experiments/edited-sound6-create-001/derived/analysis-001/capture.symbols.npz --plan experiments/replay-melodic-copy-delete-cycle-001/plan.json --out-dir experiments/compiled-melodic-copy-delete-cycle-002
```

The nine-page sample test, pending when this was written ([results](sound6-nine-page-results.md)), does not broaden these calibrated contexts.

## Copying a WAV-imported sample

The imported endpoint 17,579 now has its own exact hardware Sound6-to7 copy recapture.
The public reference-copy operation accepts either 0/17579/owner5 or 0/30912/owner5
under the existing unshared, 32,768-code Sound6-to-empty-Sound7 guards. Other endpoints,
capacities and pairs remain rejected. See
[hardware results](imported-sound6-to7-copy-results.md).

The hash-bound plan `experiments/replay-imported-sound6-to7-copy-001/plan.json` compiles
into `experiments/compiled-imported-sound6-to7-copy-001/restore.wav`, reproducing the
newly accepted WAV byte-for-byte. The compiler report remains software-only. Applying
this plan to the current already-copied artifact fails its source hash check; it is
bound to the preceding unshared mono-import source.

Deletion guards are unchanged. The next
[physical shared deletion](imported-shared-sound6-deletion-control.md) tests preservation
of the imported endpoint and full code buffer while ownership moves to Sound7.

## Shared deletion of the imported sample

Physical shared Sound6 deletion now preserves all imported codes and endpoint 17,579
under Sound7/self-owner6, matching the registered full native body exactly. The bounded
Sound6 deletion operation includes this endpoint alongside 30,912. All existing owner,
referrer, packet geometry and no-pattern-event guards remain in force. The replay plan
is `experiments/replay-imported-shared-sound6-deletion-001/plan.json`; its compiled native
body equals the genuine physical capture, with compiler hardware verification false.
A composed copy/shared-deletion plan independently reproduces that same body. See
[results](imported-shared-sound6-deletion-results.md).

Sound7 deletion at the imported endpoint remains outside the public guard. The next
[last-owner control](imported-unshared-sound7-deletion-control.md) tests removal against
an independently verified genuine empty-slot state.

## Complete imported sample lifecycle

Physical Sound7 last-owner deletion now equals the entire independently genuine
empty-slot state, preserving every unrelated packet. Both deletion contexts accept
the two separately verified endpoints 17,579 and 30,912 within their existing strict
ownership, capacity, page geometry and no-event guards. See
[final removal results](imported-unshared-sound7-deletion-results.md).

The composed `experiments/replay-imported-melodic-lifecycle-cycle-001/plan.json` compiles
into `experiments/compiled-imported-melodic-lifecycle-cycle-001/restore.wav`, byte-identical
to the previously hardware-accepted Sound4 shrink WAV. Compiler reports remain software
only. Tempo editing is unavailable; the next [control](tempo-preset-control.md) records
one BPM preset change with independently observed display values.

## Hardware-supported tempo preset plans

`{"operation":"set_tempo_preset","bpm":80}` supports the three physically observed
presets 80, 120 and 140. The generated 120-to-80 restore now matches its complete genuine
target and independently confirmed display. The writer validates both opaque global
records by calibration hashes, masking only the tempo byte; unknown contexts and fine
tempos are rejected. All unrelated sample/pattern packets remain literal. See
[preset interface](tempo-preset-edits.md) and [hardware results](generated-tempo80-results.md).

`experiments/replay-tempo80-preset-plan-001/plan.json`, compiled into
`experiments/compiled-tempo80-preset-plan-001/restore.wav`, equals the accepted WAV
byte-for-byte. Reports remain software-only; the plan binds the preceding 120 return
artifact and is rejected against the current different 80 source. The next
[physical fine-tempo control](fine-tempo100-control.md) does not broaden this scope.

## Fine-tempo integer editing

`{"operation":"set_tempo","bpm":137}` supports integer 60 to 240 in the recognized
opaque global context. The generated137 restore matches its full target and confirmed
display. Physical endpoints and representative values ground the range policy; every
integer is not individually hardware tested. Other global bytes are hash-guarded and
retained literally (tempo-edits.md; generated-fine-tempo137-results.md).

`experiments/replay-fine-tempo137-plan-001/plan.json`, compiled into
`experiments/compiled-fine-tempo137-plan-001/restore.wav`, equals the accepted WAV byte
for byte. The old preset API stays strict; the general operation handles fine sources.
Unknown swing contexts remain rejected pending suitable evidence (swing-max-control.md).

Research-only operations, not for editors: `set_raw_cell` (`pattern`, `step`, `sound`, `primary_hex`, `auxiliary`) writes one cell verbatim and `set_global_byte` (`ordinal`, `offset`, `value`) writes one byte of a global record. Used by the [stray bits observation](stray-bits-control.md).
