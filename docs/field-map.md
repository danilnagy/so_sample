# PO-33 field map

This document retains hypotheses chronologically, including their earlier unresolved
status. Native framing, calibrated sample records and bounded pattern/lifecycle edits
are now verified against genuine hardware captures. Integer tempo editing from60 to240
and swing editing from 0 to 18 are supported within recognized opaque-global contexts.
Broader slot parameters remain under investigation. See the latest entries for current scope.

## H1: reversible single-event transport changes

Experiment: event-001 A/B/A; Pattern 1, Step 1, Sound slot 9, slice key 1.
Source hashes and fixed decoder profile (sign-crossings-0.1, threshold 0.0063) are in the
capture metadata and fixture manifest. Representation: independent absolute phase labels;
units: zero-based phase-symbol indices, not protocol or state byte offsets.

Observed: both channels first change at 9309 when the event is added. Left changes end at
126936; right changes extend through most of the stream. Removing the event restores every
label in the shared A span. Returned A lacks ten terminal constant-carrier labels per channel.

Confidence: observed reversible transport association under the requested experiment.
No confidence is assigned to any unobserved state-field location. Actual button-level logs
and some UI metadata remain incomplete. Angular deltas and coordinate XOR have not localized
a pattern field. Alternatives include transport coding, validation/coding propagation,
serialized UI state, and decoder/framing interpretation. None is established.

Supporting evidence: ../experiments/event-001-results.md and its machine-readable reports.
Next independent position: event-002, same kick at Step 2. Writable fields will require
verified representation and controlled hardware restoration after modification.

## H2: candidate position-related onset spacing

Evidence: event-001 (Step 1) first diverges at label index 9309; event-002 (Step 2) at
9405, on both channels. Their empty baselines match exactly, and event-002 returns to
the full identical baseline. Observed displacement is 96 labels, or 24 packed-label bytes
per channel. These are transport units, not state offsets.

Confidence: a two-position hypothesis. No confirmed payload record size or writable field.
Alternative causes include encoded/interleaved state placement and validation/coding effects.
Step 1 versus Step 2 changed states converge after 76734/76735, while both differ widely
from empty state; this behavior does not by itself establish scrambling or compression.

Independent test registered before data collection: Step 3 onset should be 9501 per
channel if the candidate spacing continues. Full controls/counts must be checked; do not
shift streams or reinterpret the first-change definition to rescue a failed prediction.
See ../experiments/event-002-results.md and event-003-series.json.

## Step 3 prediction result (return control pending)

The user skipped fresh A and reused the previously verified empty baseline. Step 3 B
first differs at 9502 left and 9500 right. The preregistered exact index 9501 on both
channels is therefore falsified for the absolute-label first-change definition. No
shift/remapping was applied to make it fit. New A-return is pending and must be compared
with reused baseline event-002-a before attributing this solely to the edited event.

A coarser, post-observation hypothesis is that first changed packed-label byte locations
are spaced by 24 bytes per channel: floor(9309/4)=2327, floor(9405/4)=2351, and
floor(9502/4)=floor(9500/4)=2375. This agrees across three reported step positions,
but is not the original prediction and is not a decoded state-field stride. Phase-label
bit values can change the first differing symbol inside a packed byte. Transport coding
and state layout remain unresolved. Do not silently revise H2 into a confirmed field.

## Step 3 control completed

The new A-return exactly matches reused event-002-a on both channels, including all
1,970,367 labels and counts. The series deliberately lacks a fresh pre-edit A, so baseline
reuse remains documented rather than inventing a capture. The Step 3 exact-symbol
prediction remains failed; first changed packed bytes are 2375 in both channels.
Together with Steps 1/2 this gives observed 24-packed-byte spacing across three positions.
No state field is confirmed. Next investigate coding using these fixed captures and
keep first-divergence locations distinct from payload boundaries or writable offsets.

## Coding investigation round 1

Repeated-prefix periods (512 left, 128 right; first break at 8185) are verified structural
observations for the tested states, not confirmed payload framing. Bounded recurrence,
rank, word-feedback, codebook and bit-anchor probes have not yielded a payload decoder.
Clock-grid cross-checks at suitable tracking resolution agree with local counts throughout
the changed regions. See coding-investigation.md for exact windows, limits and rejected
models. No field becomes writable from these results. Next control is a repeat of the
existing Step 1 B state, not another new position; populated-state determinism remains
to be checked explicitly.

## Populated-state repeatability established for the control

Event-004-b-repeat equals original event-001-b in every phase label and exact channel
count, with no alignment or discarded symbols. The Step 1 kick differences are therefore
reproducible in the controlled dataset. Empty and populated controls are both available
for future coding/framing analysis. No algorithm or editable state field is inferred.

## Late-tail coordinate relationship

Framing round 2 identifies exact tails under a swap/inversion with opposite one-symbol
coordinate lags. Under that diagnostic relationship, empty versus Steps 1/2 differences
end at index 126936 on both channels; empty versus Step 3 differences end at 938283.
Strict raw comparisons and the failed exact Step 3 prediction are retained. No artifact
was rewritten and no payload field is inferred. See framing-investigation.md for training,
holdout windows, mapping equations and endpoint exclusions.

## Reversible staggered representation

Round 3 groups high[n+1] with low[n], making the round 2 mapping a constant circular
phase offset. All ten channels from the empty control, three positions and Step 1 repeat
invert exactly when boundary coordinates and initial phase are retained. Differences in
phase increments end at 126936 for Steps 1/2 and 938282 for Step 3 on both channels.
These are diagnostic increment indices, not writable offsets. Remaining changed spans
are still dense; no small tested linear recurrence explains them. See
staggered-investigation.md and ../experiments/staggered-probes-001.json.

## Bounded serialization/feedback results

Across Steps 1/2/3, 483840 enumerated packing/word-feedback trials did not turn the dense
changed spans into mostly matching words. The trials include raw labels, reassociated
phases/increments and four channel layouts, with independent holdouts. Some trials are
equivalent, and this is not evidence of a cipher or compression. No field is writable.
See serialization-investigation.md. Next prioritize independent waveform component
decoding rather than collecting another arbitrary step position.

## Independent amplitude-clock validation and joint-state control

An amplitude fourth-harmonic clock, using no measured crossings, agrees with all four
quarter signs throughout the checked interiors of empty, three single-kick and repeated
Step 1 captures. Existing phase labels remain supported; no additional component data
lane was found. Acquisition/edge limits are explicit in waveform-investigation.md.
Next requires the combined Step 1+Step 2 kick backup in event-005-b-joint. XOR and
modulo-four joint predictions in three fixed diagnostic views are preregistered in
../experiments/joint-predictions-001.json. Neither outcome by itself makes fields writable.

## Corrected joint control and periodic sample request

The first joint upload was a user-confirmed wrong file; joint-results-001.json is ineligible.
Corrected joint-results-002.json rejects all twelve registered predictions without fitting.
Independent quarter signs agree. Joint and Step 3 increments match after index 60010;
a limited unique displaced anchor also exists, not a general field mapping. See
joint-investigation.md for exact limits. User confirmed empty melodic slot 8. Next record
the prepared 375 Hz tone there, then a backup in event-006-b-tone, retaining the two-kick
pattern. No codec/rate is assumed.

## Partial-tone structural evidence

The user recorded about one second into empty slot8 despite full storage. The new backup
is valid, longer, and independent quarter checks agree. First raw change is829509; a
520-increment period occurs in a longer body region, but a shorter region already existed
before sampling. A +100362 diagnostic displacement gives a shared exact tail. Bounded
CRC hypotheses fail held-out blocks; no checksum/frame format is accepted. See
tone-investigation.md. Next needs ordinary Sound8 playback to verify retained tone content;
current memory is preserved.

## Playback control completed; minimal baseline prepared

Sound8 ordinary playback is a clean1.26-second tone at~561.946 Hz, compared with the
375 Hz input. The pitch ratio suggests transposition; it does not establish the actual
native duration or codec rate. No repeating backup region is promoted to sample data.
The next series, empty-001, starts from reset settings with sounds/patterns explicitly
cleared and two unchanged-state captures. See empty-baseline.md. Hardware changes are
pending, and every original capture/playback source remains preserved.

## New minimal-state pair validated

empty-001-a and its consecutive repeat have identical45033 complete phase labels per
channel and identical partial final intervals at threshold0.0063. Independent amplitude
clock checks agree. The transfer is much shorter; no internal all-zero payload is assumed.
Bounded single-state probes did not recover a small recurrence. See
../experiments/empty-001-results.md. Next add only the full calibration tone to Sound8,
retain empty patterns and record two consecutive backups per empty-tone-control.md.

## Minimal one-tone pair validated

The Sound8-only pair matches178847 complete labels per channel and partial endpoints.
Both channels preserve the empty baseline through43353 and first differ at43354.
The enlarged body does not show a strong tone repetition in tested raw/reassociated
views, so no region is labeled native sample data. See minimal-one-tone.md. Next copy
the stored sound8 to empty sound1 and capture once, testing slot/content reuse without
a new analogue recording. Copy/allocation semantics remain unverified.

## First Sound1 copy observed

Copied state has178868 labels per channel, only21 more than Sound8-only. A-84 diagnostic
offset locates100350 identical increments per channel with zero circular phase offset.
First strict change is43270 versus43354 for the earlier slot8 addition, motivating an
unverified12-label sound-slot spacing. No pointer or codec is accepted. See
copy-investigation.md. Second destination2 predictions are pinned before capture in
../experiments/second-copy-predictions-001.json, with competing front-table/inline windows.

## Sound2 capture with reported recovery steps

The user deleted8, copied1 back to8, then8 to2. This extra history is retained as a
confound; the single-action prediction is not declared validated. Observed first changes
177093/177092 fall in the inline window, small count growth is32, and six anchors match.
No pointer or native codec is verified. See ../experiments/empty-001-d-copy-to-2/validation.md.

This capture exposed a leading-silence acquisition bug: decoder0.1's implicit negative
origin at file zero could invent a long run. Version0.2 uses the first thresholded sample,
preserves all prior phase goldens and keeps real long-gap rejection. A fresh before/after
pair after deleting only2 is requested per clean-copy2-control.md. Original predictions
and the deviated source recording remain unchanged.

## Clean Sound2 copy validated against registered windows

Fresh clean-a matches all178868 complete labels per channel of original copy1;
clean-b matches all178900 of the earlier deviated endpoint. The new single-action pair
passes the saved inline window (first changes177093/177092), fails the front-table window,
adds32 complete labels and preserves all six anchors. Original deviation history remains
unchanged. Independent waveform interior checks agree. See clean-copy2-results.md.

Both copy operations move the last nonzero increment by28, whereas complete-count growth
also includes variable constant carrier. A12-empty/40-populated transport-record model is
now proposed and registered for a copy into Sound3. It is not a native descriptor size or
safe writable field. See third-copy-control.md; one hardware capture is required next.

## Sound3 spacing prediction passed

The Sound8-to3 copy first differs at177133/177132, exactly40 later than Sound2's changes.
The last nonzero increment is178792 on both channels, exactly28 later, and all six anchors
are preserved. Complete-count growth22/21 includes a shorter constant carrier section.
This validates the registered transport-spacing predictions, not native payload fields.
Adjacent40-position regions lack a literal or fixed-permutation template in the tested
views. See third-copy-results.md. A Sound3 minimum-length trim is now registered as the
next parameter control, retaining all stored sounds; see sound3-trim-control.md.

## Sound3 minimum-length trim observed

First raw difference177147 on both channels lies inside the registered Sound3 window.
Shared content prefix and all six anchors survive, and the last nonzero increment remains
178792. Count growth0/+1 is terminal carrier variation. The changing tail remains dense;
twenty binary difference recurrence fits exceed degree256. No native writable trim field
is accepted. See sound3-trim-results.md. A maximum-length return control now pins the
original nonconstant prefix separately, so size/anchor matches alone cannot count as
returning to the original state; see sound3-trim-return-control.md.

## Maximum-length return prediction failed

The maximum-length capture is clean and preserves the shared content, but differs from
original untrimmed Sound3 first at177148 on both channels. Its original-prefix return
check fails despite passing minimum-to-maximum onset, count allowance and anchors.
Last nonzero increment is178791 left/178792 right; that coordinate is not a parsed
payload length. Further bounded recurrence probes do not recover coding. See
sound3-trim-return-results.md. A separate copy8-over3 return is now registered to test
whether copying replaces the relevant settings; the failed knob-return result remains.

## Copy-based Sound3 return confirmed

The copy8-over3 capture matches original E's full complete-label arrays and counts
(178922 left,178921 right), beyond the required prefix/anchor checks. This establishes
the return path for this controlled trim series, not native fields or arbitrary editing.
The maximum-knob return remains failed. A concrete PO-32 CRC-additive whitening lead
was audited and tested on existing empty data; no constant-plaintext16-byte run validates
within the2304 enumerated views/packings. See sound3-copy-return-results.md and
related-whitening-investigation.md. Next measure ordinary playback of the retained full
tone from this cleared series, keeping it distinct from the older memory-full sample.

## Native framing and controlled trim value recovered

Right-first alternating stereo increments, with negative circular mapping, expose CRC-
additive whitening and checksum-validated packets. The authoritative corpus verifies
56,090 checks across24 registered-source captures; original phase artifacts remain unchanged.
Sound3 minimum trim differs in one0xEF78 packet's little-endian bytes4..7:64704 becomes79.
Maximum is65456; copy return restores64704. At start zero this is a B-controlled boundary;
nonzero-start and inclusive-end semantics remain unverified. Re-encoding the minimum
reproduces its recorded packet body and required phase prefix exactly.

Signed-complement mu-law at nominal23437.5Hz recovers the375Hz tone from the stored buffer.
Playback561.954Hz/1.25s is consistent with transposition of1.87s audible stored tone.
The new generated candidate sets only Sound3's counter8000; all other packets and sample
bytes are unchanged. Software full-label/count and packet roundtrips pass, with172 tests
passing overall. Hardware restore is the next required validation. See packet-decoding.md
and native-trim-restore-test.md. No general GUI or arbitrary sample replacement is claimed.

## Native trim edit accepted and recaptured exactly

The edited-trim-001 capture validates all511 native packet checksums and matches the
generated target body SHA-2560191ad7ee47710d5bcb117d8b3d1c9774c972ff06df829f9cb302d2f2046c4d7.
Only original plain packet375 changes, setting Sound3's counter8000. Sounds1/2/8 remain
64704 and the65536-code owner buffer is unchanged. The user reports successful restore
and the requested short/long tone checks. This establishes this zero-start trim edit
and canonical carrier on the local hardware path. The unedited control remains untested.
See ../experiments/edited-trim-001/hardware-validation.json.

An experimental writer now replaces an existing owner buffer at its exact original size,
preserving all header bytes, packet sizes and unrelated payloads. Signed-complement
mu-law encoding maps nearest representable levels without gain normalization. The next
candidate imports750Hz/2s PCM audio into the existing shared owner, so Sounds1/2/3/8
all receive the new tone, with their validated trim counters unchanged. Full software
roundtrip passes; sample writing needs separate hardware evidence. See
native-sample-restore-test.md. Nonzero-start semantics and buffer allocation remain open.

## Fixed-size sample replacement accepted and recaptured exactly

The edited-sample-001 capture matches the generated750Hz candidate's complete native body
SHA-256 `8f851166868fd99e7935a5942a2b82181f0268c3a05303f08852a0f06ebb30a0`
and every backing code, with511 valid checksums. All sound headers, counters, packet tags
and payload lengths remain unchanged. Only owner data packets change from edited-trim-001.
The user completed the restore/listening/recapture protocol; detailed acoustic observations
were not supplied. See ../experiments/edited-sample-001/hardware-validation.json.

## Native pattern layout exposed by existing kick controls

Each pattern has1032 concatenated0xC498 payload bytes: a candidate768-byte primary region,
256-byte auxiliary region and8-byte opaque footer. Pattern1's kick controls have identical
12-byte primary data at offset24 for Step1,72 for Step2 and120 for Step3. Auxiliary changes
occur at776,792 and808 respectively. Step1/3 and the corrected joint state use value16;
the Step2-only state uses17. The difference remains unresolved.

Retrospective relocation of Step1's raw primary and auxiliary rows reproduces the whole
Step3 and corrected joint packet bodies exactly; it does not reproduce Step2-only because
of the auxiliary difference. Old phase-domain failures are retained. `inspect-patterns`
reports raw regions without interpreting sound, pitch, timing, volume or effects. No
pattern restore is validated yet. A single Sound3 melodic event at Pattern1 Step1 is
registered against the freshly verified empty pattern baseline; see melodic-step1-control.md.

## Melodic control passed; first pattern edit candidate prepared

The Sound3/key1 Step1 capture changes only Pattern1 bytes6/7/8 to0D/F8/83 and byte770
toF0. All registered locality/preservation checks pass, with511 valid packet checksums
and unchanged sample data. The Sound3 offset6 and Sound9 offset24 support16 three-byte
sound-indexed cells in each48-byte primary step row, paired with one auxiliary byte per
sound in each16-byte auxiliary row. This mapping is supported locally for Sounds3/9;
other slots and all packed bit meanings remain untested. The earlier12-byte groupings
were diagnostic subdivisions, not established voice records.

An experimental writer copies both whole opaque source rows into completely empty target
steps, with a single matching primary/auxiliary cell required. Source rows, footer, samples,
other patterns, packet tags and lengths are preserved. Genuine single-kick Step1-to2
cloning reproduces the corrected joint native body exactly. The new melodic candidate
retains Step1 and adds5/9/13, passing full software roundtrip and all511 checksums; hardware
acceptance is pending. See melodic-step1-results.md and native-pattern-restore-test.md.
The drum Step2 auxiliary discrepancy remains unresolved and is not normalized away.

## Four-note generated pattern accepted by user; recapture pending

The user explicitly reports that restore and expected four-note playback worked. This
confirms local hardware behavior for the opaque Sound3 step copies at1/5/9/13. The expected
edited-pattern-001/capture.wav is not yet present, so no new packet-body or sample-preservation
result is claimed. The existing software checks remain historical software evidence.
See ../experiments/edited-pattern-001/hardware-observation.json.

The prepared recapture validator requires the real capture and its reviewed artifact,
then checks the registered body hash, all packet data, samples, other patterns, copied
rows and populated steps. Focused tests accept the software target only as a comparison
vector and reject both an unedited backup and a checksummed sample change. No hardware
report is written until real recapture inputs are available. Further device edits wait
for this backup; see native-pattern-restore-test.md.

## Four-note pattern recapture verified after playback

The user supplied the backup and explicitly reports recording after pattern playback.
The full native body equals the generated target SHA-256
`8b39765df9a4caf71e509f54b0c49e2f0d95ad1a60f4effa46daa687259d0104`, with511 valid
checksums, unchanged samples and other patterns, and identical raw source rows at1/5/9/13.
No playback-induced native differences were observed; no masking or normalization was
applied. The source WAV hash is
`494957d160d0454eef3db5273e05496c59f98b6da89c0dc6bb25ee9115c182af`.
See ../experiments/edited-pattern-001/hardware-validation.json and capture-context.json.
This completes local hardware validation of this opaque step-copy candidate.

A single-key replacement control now keeps Pattern1 Step5 and Sound3 fixed while changing
keyboard key1 to2. Samples, other notes and unrelated packets should remain unchanged.
The low-nibble key-index hypothesis predicts auxiliary byte834 F0→F1 with primary bytes
0D/F8/83 unchanged. It remains a registered hypothesis; no note bitfield writer is enabled.
Control invariants and hypothesis fits must be evaluated separately. See melodic-key2-control.md.

## Key2 mapping fit and first generated note-key edit prepared

The fixed-Step5 Sound3 key2 capture changes only auxiliary byte834 F0→F1. Primary
0D/F8/83, samples, Steps1/9/13, other patterns and all unrelated packets remain unchanged.
All511 checksums validate; both registered hypotheses fit separately from the control
invariants. This supports index0/1 for Sound3 keyboard keys1/2, while the auxiliary upper
nibble and all primary bitfields remain opaque. Other keys and sound slots remain untested.

The `set-note-key` writer accepts only those observed keys, primary0df883, auxiliaryF0/F1
and one matching source cell. It rejects untested inputs, preserves all unrelated bytes
and reproduces the full genuine key2 body and inverse key1 body exactly. The first
generated key candidate changes only Step13 byte962 F0→F1, giving keys1/2/1/2 across
Steps1/5/9/13. Full software waveform/count and packet roundtrips pass; its hardware
restore/playback/recapture test is still required. See melodic-key2-results.md and
native-note-key-restore-test.md. The old drum auxiliary10/11 observation is not retroactively
assigned a confirmed physical slice selection.

## Generated key edit verified with measured-clock recovery

The user confirms alternating pitches and supplies the backup. The original0.0063
crossing decode fails CRC at wire byte13130, with its first independent left-clock
disagreement at label26472. The failed artifact remains in analysis-001. The new
amplitude-clock-0.1 artifact in analysis-002 samples waveform quarter signs and uses
only a unique2048-label pre-frame alignment. It passes all interior quadrature relations
and all511 native checksums. Its complete body exactly matches the generated91b37d61...
target, with only the expected source byte962 F0→F1 changed. Samples and other note
parameters are unchanged. User-confirmed musical behavior and this exact comparison
complete local key1/2 field-edit validation.

The measured-clock method independently reproduces all24 existing corpus bodies and
56,090 checksums. No target data or checksum repair guides decoding. Its artifact has
fixed windowed coverage with explicit unobserved edges; direct waveform encoding is
rejected, and verified-packet rebuilding is required. Source captures and failed artifacts
remain unchanged. See measured-clock-recovery.md.

The next fixed-Step5 Sound3 control replaces keyboard key2 with16. It predicts primary
0df883 unchanged and auxiliary834 F1→FF, but full4-bit key support remains unverified and
disabled. The reviewed baseline is the new measured-clock analysis-002, not the failed
crossing artifact. See melodic-key16-control.md and ../experiments/melodic-key16-predictions-001.json.

## Far keyboard endpoint passed; middle-key control registered

The Sound3 Step5 key16 capture changes only auxiliary834 F1→FF, leaving primary0df883,
samples, other notes, other patterns and all unrelated packets unchanged. Both registered
hypotheses fit separately from the passing preservation checks. The initial crossing
decode fails at17902 and is preserved; measured-clock analysis002 independently validates
all511 packets and yields body55311018711e4b4b798609ce7c40bedb613d6dbb246ea2423aea8b8049db9fe9.
See melodic-key16-results.md and ../experiments/melodic-key16-results-001.json.

The observed Sound3 key mapping is1→F0,2→F1,16→FF, consistent with low-nibble indices
0/1/15. The upper nibble remains opaque. Middle keys and generated key16 behavior remain
untested; the writer is not expanded in this step. The next fixed-Step5 control replaces
key16 with7 and predicts FF→F6 while primary and unrelated state stay unchanged. Its
baseline is the newly verified measured-clock endpoint artifact. See melodic-key7-control.md
and ../experiments/melodic-key7-predictions-001.json.

## Independent middle key passed; four calibrated values supported

The key7 control changes only auxiliary834 FF→F6, with primary0df883 and all unrelated
state unchanged. Its normal0.0063 crossing decode validates all511 packets without
measured-clock recovery. Both registered hypotheses fit separately from all control
invariants. Body SHA is6b4f5fd40b5b7c66a754c7a6f2d870015e69e225f24a2fe9730a6f3a135705ff.
See melodic-key7-results.md and ../experiments/melodic-key7-results-001.json.

The writer now supports only physically observed Sound3 keys1/2/7/16 with auxiliary
F0/F1/F6/FF, a single matching source cell and primary0df883. Other keys, sounds and source
parameters remain rejected. Genuine endpoint/middle forward and inverse packet bodies
are reproduced exactly. The next generated phrase assigns1/2/7/16 to Steps1/5/9/13,
changing only auxiliary834/898/962 and preserving all other data. Full software checks
pass; the generated use of keys7/16 awaits restore, manual pitch comparison and recapture.
See native-four-keys-restore-test.md. No all16-key or gate-field support is claimed.

## Four calibrated key edits verified on hardware

The user confirms Pattern 1 matched manually auditioned Sound 3 keys 1/2/7/16.
The genuine recapture SHA-256 is
`2cc8b8df219f49e9a0721d67ecf719c37575f9f9da7f264eac5b2c4736eb84bf`.
Its entire native body exactly equals the generated target
`9b87309f572b188cd1e1a2651b1ca4feec5cfa8fb669068631042ca8f49465f0`, with 511
valid checksums and only the three registered auxiliary byte changes from the key 7
baseline. Samples, note primary fields, upper auxiliary nibbles and all unrelated
packets remain unchanged. Measured-clock recovery is independent of the target;
the failed crossing artifact at wire byte 9941 is preserved. See native-four-keys-results.md.

The next registered control adds Sound 2 key 1 to Pattern 1 Step 1 while preserving
its Sound 3 key 1 note. Only candidate primary bytes [3,6) and auxiliary byte 769
may change. Values 0df883/F0 are separate unverified hypotheses. This tests another
sound cell and coexistence of cells on a step; no Sound 2 or multi-sound writer is
enabled by the prediction. See sound2-layer-control.md.

## Sound 2 added; primary-equality hypothesis rejected

The physical Sound 2 key 1 addition changes only Pattern 1 bytes 3/4/5 from zero
to 0D/28/31 and auxiliary 769 from zero to F0. Preservation and locality checks
pass, with Sound 2 and Sound 3 cells coexisting on Step 1. The primary-equality
hypothesis fails; the auxiliary hypothesis and packet indices 4/7 match. Original
predictions and the failed result remain unchanged. No primary-field meanings are
assigned. See sound2-layer-results.md.

The normal crossing decoder validates all 511 packets. Capture SHA-256 is
`34b9b78a92d62e76383ee2bd673ae1590793e10b2376ed2dd19974d8c1d16549`, native body is
`e2d6c4a33c045deec30c27449a39182dc6bd0fb80bbe002aba85b0678ce4681d`.

The experimental cell-copy operation preserves actual Sound 2 primary0d2831 and
auxiliaryF0 intact. Only empty Sound 2 targets and optional calibrated Sound 3
neighbours are supported. Unknown cells and parameters are rejected. The generated
Step 9 addition changes only bytes387/388/389/897 in packets5/7, preserving Sound 3
key7 there. Software checks pass; its hardware test remains required. See native-sound-cell-restore-test.md.

## Sound 2 cell copy verified; bounded removal prepared

The user confirms the Sound 2/Sound 3 light checks and normal playback. The recapture
matches the entire generated body4362aa66... with 511 valid checksums and only the four
registered added bytes. Samples and all previous note cells remain identical. The normal
crossing decoder validates it directly. Capture SHA-256 is
`1adb6964a06f239adfcd599c2996b6d2d075e67576e63955e150ec8c5d84b56f`.
See native-sound-cell-results.md and the separate hardware-validation.json.

`remove-sound-cell` now experimentally clears only an occupied observed Sound 2
0d2831/F0 cell, preserving any calibrated Sound 3 neighbour. Its inverses reproduce
the entire genuine one-cell control and four-key baseline exactly. Unknown, empty and
partial cells are rejected. The new candidate clears Sound 2 on Step 1 only, retains
Sound 2 on Step 9 and all four Sound 3 notes, and changes just bytes3/4/5/769 in
packets4/7. Software checks pass; generated-removal hardware acceptance remains pending.
See native-sound-cell-removal-test.md. Primary-field meanings and other sounds remain open.

## Sound 2 removal verified and read-only project exported

The user confirms the removal light/playback checks. The genuine recapture equals
the whole generated1e493f14... target with all511 checksums, only bytes3/4/5/769 cleared,
and Sound 3 at Step1 and Sound 2 at Step9 preserved. Samples, headers and unrelated
packets are identical. Capture SHA-256 is
`aa8c083704bb92aa44893bafc3abd35e2bc05182fbb01ca7511f04752dafeb7d`.
See native-sound-cell-removal-results.md and the separate hardware comparison.

The read-only project export preserves all raw packets/source files and provides 16
pattern views and four zero-start sample previews. Unknown fields remain raw, and the
export report is not new hardware evidence. See project-export.md.

The next physical control moves only Sound 3's TRIM knob A, preserving knob B and all
other state. The first reference field is hypothesized to become nonzero; alternative
second-field hypotheses are evaluated separately. No nonzero-start sample writer or
extractor is enabled. See sound3-start-control.md.

## Nonzero start control passed; second-field alternatives failed

Only the Sound 3 reference changes from00000000401f000000 to a17a0000ffff000000,
at plain packet375 offsets0/1/4/5. Every pattern, sample code, owner and unrelated
packet remains unchanged. All511 checksums pass the normal decoder. The user still
hears the tone, without an independently measured duration. First field31393 fits
the start-response hypothesis; second65535 contradicts both constant8000 and
first+8000. No endpoint, length or special-maximum meaning is assigned.
See sound3-start-results.md and the unchanged original prediction report.

The new read-only export preserves the nonzero-start record and marks its preview
unsupported. The next fixed-start knob B minimum control independently predicts
second79 or start+79=31472, based on the genuine zero-start minimum. No nonzero-start
sample reader or writer is enabled. See sound3-start-min-control.md.

## Fixed-start minimum preserved; exact values failed, local endpoint inference supported

The first field remains31393 and the second becomes31504, raw width111. Only reference
packet375 bytes4/5 change, with all other state preserved and511 valid checksums. Exact
predictions79/31472 both fail and remain unchanged. The user subsequently reports a very
short click/burst from Sound 3 key1, supporting a local endpoint interpretation without
an independent duration measurement. See sound3-start-min-results.md and audition-observation.json.

The writer is bounded to Sound 3/start31393/owner0/65536 codes and endpoints31504..65535.
It reproduces both whole genuine endpoint bodies and inverses. Other starts and ownership
are rejected; a general minimum rule and endpoint inclusivity remain unresolved. A separate
preview explicitly uses half-open[start,end). The default project exporter retains its prior
zero-start-only preview policy. The generated endpoint39393 edit changes only two reference
bytes, preserving samples and patterns; its separate hardware test is pending. See native-nonzero-trim-restore-test.md.

## Fixed-start endpoint hardware verified; guarded plan replay added

The user confirms brief Sound 3 and unchanged longer Sound 8 tones. The genuine recapture
exactly equals the b3296f2e... target with511 valid checksums, start31393/end39393 and
all backing codes, other sounds and patterns preserved. Capture SHA-256 is
`7935f7cfe3ab7a8b8d45dbe942f3144dad2c7eebb09c8aa52fb06f96a1d632d8`.
See native-nonzero-trim-results.md. Inclusive/exclusive endpoints and general starts/minimum
rules remain unresolved; the earlier failed exact predictions are retained.

Explicit project-export opt-in now includes the calibrated preview. Hash-bound JSON plans
apply only existing guarded writers, and the replay exactly reproduces the accepted WAV
bytes. No new device operation is claimed by replay. See edit-plans.md. The next physical
quarter-position knob A control probes another start without broadening the writer yet.

## Second nonzero start observed

The quarter-position control passes all preservation checks with reference
`c42d0000332e000000`: first11716, second11827, owner0. Only packet375 changes;
all backing codes, other sounds and16patterns remain identical. The lower-first-field
prediction passes; both second-field alternatives39393/65535 fail. Width111 repeats
the earlier physical minimum, but does not establish a general minimum rule or isolated
knobB response. See sound3-start-quarter-results.md.

A separate hash-pinned candidate sets only this reference's endpoint to19716, keeping
start11716 and selecting8000codes under the explicit preview convention. Strict waveform
and whole-body roundtrips and its exact inverse pass. Hardware acceptance is pending
(native-quarter-window-restore-test.md); public writers retain start31393 scope.

The clean second-start retry now matches the entire933eca1c... target with511 valid
checksums and user-confirmed restore/tone checks. Both discrete Sound3 starts are supported
with separate local endpoint bounds:31393→31504..65535 and11716→11827..19716. Explicit
window repositioning reproduces both independent hardware bodies and the replay equals
the accepted second-start WAV byte for byte. No interpolated starts or general minimum
rule is enabled. See native-quarter-window-results.md. Drum selector mapping is the next
separately registered control (drum9-copy-control.md).

## Sound9 copy localizes a sixteen-record block

The physical Sound1→Sound9 copy adds one9-byte EF78 reference under each selector8..23,
all owner0. All prior packets/data outside these groups remain identical. Native packet
count grows511→527 and body bytes grow224, with527 valid checksums and bodyf83e2157...
The all16-populated hypothesis passes; first-group-only fails. Second fields advance
4044 per record to64704; first fields are0 then previous-second+1. This is a post-capture
observation, not a general autoslice or inclusivity rule. See drum9-copy-results.md.

The read-only view now groups this complete block under Sound9. Other drum-slot mappings
and individual key ordering are explicitly unverified; no drum writer/preview is enabled.
The next physical control selects Sound9 key1 and changes only knobB to minimum,
testing selector8 mapping and the independently registered79/lower-than4044 alternatives.

## Sound9 key1 maps to selector8; minimum field127 observed

The single-slice minimum control passes every preservation check with527 valid checksums.
Only packet383/selector8 changes, reference00000000cc0f000000→000000007f00000000;
start0 and owner0 remain intact. Mapping/lower-value hypotheses pass; exact79 fails.
The other15 references, all backing codes, melodic sounds and patterns are unchanged.
See drum9-key1-trim-min-results.md. No general drum minimum or inclusivity rule is inferred.

The experimental writer accepts only this zero-start key1 reference with owner0/65536
codes and the literal other15 copy records, guarded to endpoint127..4044. It reproduces
the whole genuine minimum/copy bodies and inverses. A first candidate endpoint2000
passes strict waveform/body checks and awaits native-drum9-slice-end-restore-test.md.

The first generated endpoint2000 now has an exact whole-frame hardware recapture:
527 valid checksums, body4eca78dc..., only packet383 changed from the minimum source,
and both requested tones user confirmed. See native-drum9-slice-end-results.md.
Explicit export opt-in now previews the calibrated key1 raw codes, with unpitched
half-open extraction; no other drum preview or writer scope is broadened. The next
key2 minimum control tests selector9, first4045 and exact second127 versus4172 alternatives,
with a separate broad endpoint-range prediction and post-capture acoustic discriminator.

## Drum key2 maps to selector9; exact endpoint prediction passes

The next minimum control passes all preservation checks with527 valid checksums.
Only packet385/selector9 changes, referencecd0f0000981f000000→cd0f00004c10000000:
first4045 remains, second4172 equals the exact registered4045+127 endpoint prediction.
Literal-length127 fails. The user reports a click after saving, supporting a short
local window; exact duration and inclusivity remain unresolved. Key1 endpoint2000 and
all other state are intact. See drum9-key2-trim-min-results.md.

The experimental writer now permits keys1/2 at their separate fixed starts and intervals,
with the remaining14 original-copy records guarded literally. It reproduces the complete
genuine key2 minimum and baseline bodies/inverses. A first key2 endpoint6045 candidate
passes software waveform/body checks and awaits native-drum9-key2-end-restore-test.md.

The key2 endpoint6045 candidate now passes an independent clean hardware recapture:
527 valid checksums, exact body1f3295c4..., key1 reference2000 preserved, both Sound9
tones user confirmed. The first failed WAV/artifact remain archived and acceptance uses
the separate retry. See native-drum9-key2-end-results.md. Explicit export opt-in now
previews both controlled slices with unpitched half-open selections. The next Sound1→Sound10
copy probes inferred selectors24..39 and exact original-autocopy record equality while
preserving all existing buffers, references and patterns (drum10-copy-control.md).

## Sound10 confirms the second sixteen-record block

The clean Sound1→Sound10 copy passes all registered checks/predictions with543 valid
checksums and body9e2801c1... Only selector24..39 data is added, sixteen9-byte owner0
references equal to the original Sound9 autocopy before trims. Packet count grows16
and native body224bytes; both accepted Sound9 windows and all other state are intact.
The failed first waveform and diagnostics remain archived. See drum10-copy-results.md.

The Sound10 block is now grouped observed in the read-only view, but individual key
order, writer and preview remain disabled. The next control copies last-triggered
Sound9/key1 into Sound10/key1, independently testing selector24 and raw reference
copying while preserving all other records (cross-drum-slice-copy-control.md).

## Sound10 key1 maps to selector24; physical reference copy is exact

The physical Sound9/key1 to Sound10/key1 copy changes only packet415/selector24,
reference00000000cc0f000000 to00000000d007000000. All543 native checksums and all
saved mapping/verbatim-copy/byte-change predictions pass. Other15 Sound10 references,
all Sound9/source/backing data, patterns and every other plain packet remain identical.
See cross-drum-slice-copy-results.md. Only Sound10/key1 keyboard mapping is promoted.

The bounded reference-copy writer reproduces both whole genuine bodies and an inverse
using the already calibrated source endpoint edits. It permits Sound9/keys1 or2 into
existing Sound10/key1 under local-window and literal-neighbor guards. A generated
key2 nonzero-start transfer passes software roundtrips and awaits
native-cross-drum-slice-copy-restore-test.md. Other keys/slots, allocation, Sound10
endpoint editing, previews and exact endpoint inclusivity remain unsupported/unresolved.

## Generated nonzero-start Sound10 key1 reference copy accepted

The full recapture equals body846092c0... with543 valid native checksums. Only
packet415 receives the accepted Sound9/key2 referencecd0f00009d17000000; all other
references, backing codes, sounds and patterns are unchanged. User-confirmed restore
and tone checks are recorded separately (native-cross-drum-slice-copy-results.md).

Opt-in raw preview now supports Sound10/key1 only at the two accepted copied windows,
with the local copy context and literal other15 destination records. The copied
nonzero preview equals Sound9/key2 byte for byte. No destination endpoint editing,
arbitrary drum mapping or allocation is introduced. The next Pattern1/Step1 Sound10/key1
control tests the candidate cell10 and F0 auxiliary against independent row/sample
preservation checks; raw melodic primary comparisons remain unverified hypotheses
(drum10-note-control.md).

## Sound10 drum note maps to cell10; auxiliary10 differs from melodicF0

The physical Pattern1/Step1 addition passes all preservation checks with543 valid
checksums/bodyedd7c74f... Only bytes27/28/29 become0df883 and auxiliary777 becomes10;
packets4/7 change. Sound10 cell10 and Sound3-primary hypotheses pass, while F0 auxiliary
and Sound2-primary comparisons fail. All existing notes, samples/references and other
plain packets are unchanged (drum10-note-results.md).

The exact observed pair identifies drum slice1 in the read-only view, separately from
melodic key projections. A bounded opaque copy/removal writer supports Pattern1/Sound10
in the accepted nonzero copied-window context, with calibrated Sound2/Sound3 neighbors.
Whole genuine bodies and inverses are reproduced. The first generated Step9 copy
awaits native-drum-cell-copy-restore-test.md; key/parameter bitfields and arbitrary
drum patterns remain unresolved.

## Generated Sound10 key1 copy into a three-sound Step9 accepted

The full recapture equals body6f4e2cab... with543 valid checksums and user-confirmed
grids/playback. Only Pattern1 bytes411/412/413/905 and packets5/7 change from the source.
Step1/key1, both melodic Step9 notes, all other events and samples/references remain
intact (native-drum-cell-copy-results.md). Existing bounded writer scope is retained.

The next independent control replaces only the Step9 Sound10 note with keyboard key2,
testing primary retention and exact auxiliary11 versusF1 alternatives. Step1/key1 and
all other state must remain identical. No key2 writer/projection or general upper-nibble
meaning is enabled before results, and this note control does not map the Sound10/key2
sample-reference selector (drum10-step9-key2-control.md).

## Sound10 recorded key2 changes auxiliary10 to11

The physical Step9 replacement passes all preservation checks with543 valid checksums,
body1ca33191... Only auxiliary905 changes16 to17; primary0df883 and all other state
remain identical. Exact drum11/one-byte/packet7 predictions pass; melodicF1 fails.
The read-only view recognizes the two exact recorded-key pairs, while Sound10/key2
sample-reference mapping and generated key2 editing remain unsupported
(drum10-step9-key2-results.md).

The next control records an independent half-second1000Hz sample into empty Sound4.
New self-owner3 and preservation of old owner0 are separately registered hypotheses;
actual buffer size/padding and possible relocation/global bookkeeping will be reported
without a predetermined allocation rule. No allocator/resizing writer is enabled
(sound4-allocation-control.md).

## A second independent32768-code buffer is owned by Sound4

The physical recording passes all registered controls/hypotheses with679 valid
checksums/body523f2dd9... Only selector3 gains32777 bytes in136 packets, with header
00000000c06f000003 (0/28608/owner3) and32768 sample codes. Old owner0's65536 codes,
all existing references/notes, global packets and patterns remain identical. The
decoded tone independently fits1000.033Hz (sound4-allocation-results.md).

Capacity exceeds the endpoint by4160 codes;3974 are nonzero code bytes. Preserve them
without calling them zero-byte padding or inferring audible/stale contents. Two buffer
sizes do not establish rounding, reuse or resizing behavior. The next Sound4-to5 copy
tests a retained owner3 reference before re-recording the original owner at a different
length (sound4-to5-copy-control.md). No allocator writer is enabled.

## Sound5 confirms reference sharing of independent owner3

The physical copy adds only selector4's exact nine-byte00000000c06f000003 reference.
680 native checksums pass, bodyeb19589f..., native growth14bytes/one packet. Both owner
buffers, all other records and patterns remain intact. Three fixed profiles agree after
the original profile fails acquisition; source/diagnostic history is preserved
(sound4-to5-copy-results.md).

The next control re-records only Sound4 with a longer1250Hz tone while Sound5 remains.
Logical old-window preservation, full transfer to owner4 and tracking the new source
are independently tested, without an assumed capacity or allocation formula. Unknown
window layouts and lost copies remain reported observations. No allocator/resizing
writer is enabled (shared-sound4-rerecord-control.md).

## Shared re-recording transfers old data and allocates a larger new owner3 buffer

985 checksums pass/bodybe92460f... Sound4 becomes0/72128/owner3 with73728 codes;
Sound5 becomes0/28608/owner4 with the entire old32768-code buffer, including its tail,
unchanged. Only selectors3/4 change; all other sounds, patterns and non-source packets
are identical. Full transfer/preserved-window hypotheses pass; shared tracking fails
(shared-sound4-rerecord-results.md).

All complete owned packet sequences match4096-code pages split into255-byte payloads
and their25-byte first-page/16-byte later remainders. This is packetization evidence,
not a capacity-selection rule. The73728 capacity is non-power-of-two. Sound4 is now
unshared; the next short re-recording separates capacity shrink/reuse from endpoint
reduction without disturbing independently owned Sound5 (unshared-sound4-shrink-control.md).

## Unshared re-recording releases capacity; generated growth test pending

The short replacement passes815 checksums/body160983f6... Only selector3 changes,
from73728/end72128 to32768/end30912, remaining zero-start self-owner3. Sound5's entire
buffer/header, all other sounds/patterns and non-Sound4 packets stay identical.
Capacity reuse fails; both4096/8192 divisibility hypotheses pass, leaving minimum
allocation units unresolved (unshared-sound4-shrink-results.md).

A research-only generated probe reuses the larger device header and ordered chunk
geometry while substituting a1750Hz,3.08second tone. Reconstruction with old template
codes reproduces event024's entire body; the new sample passes software waveform
roundtrip and locality checks. Device testing is pending (sound4-generated-growth-control.md).
This does not enable general allocation or shared-owner resizing.

## Generated unshared growth matches hardware; inverse shrink pending

The generated Sound4 growth is accepted with985 native checksums and complete body
5e6946b2... exact. All new1750Hz sample codes and the zero tail survive; Sound5,
other sounds and every pattern are unchanged. Separate user-confirmation and hardware
acceptance reports preserve software-report provenance (sound4-generated-growth-results.md).

The research helper now permits both directions between the exact32768/end30912
and73728/end72128 layouts under unshared owner3, reusing device-derived packet geometry.
The pending generated shrink targets the smaller layout with a2250Hz,1.32second tone.
Substituting the old physical smaller buffer reproduces that capture's entire body;
the synthesized shrink also passes software roundtrip checks. General allocation and
shared-owner operations remain unsupported (sound4-generated-shrink-control.md).

## Generated shrink accepted; empty Sound6 self-owner creation pending

The inverse Sound4 resize now passes815 hardware checksums with entire body12acce04...
exact. Every generated2250Hz code and zero tail byte survives, with all unrelated
sounds, patterns and plain packets unchanged. User audible checks are confirmed
(sound4-generated-shrink-results.md). Both known unshared resize directions are verified.

The next research probe populates existing empty selector5/Sound6 with32768 codes,
header0/30912/owner5 and a generated500Hz tone. It copies observed Sound4 page geometry
without changing globals or selectors. The same insertion algorithm independently
reconstructs the earlier real empty-Sound4 capture exactly, but Sound6 creation itself
needs hardware confirmation (sound6-generated-creation-control.md). Capacity selection,
deletion and shared-owner edits remain unsupported.

## Empty Sound6 creation accepted; generated Sound7 sharing pending

The generated Sound6 creation now passes951 hardware checksums and matches complete
body258bb81f.../all plain packets. Selector5 owns32768 codes with0/30912/owner5; all
generated500Hz codes/tail bytes survive, and every existing record/pattern/global
packet remains exact. User audible checks are confirmed (sound6-generated-creation-results.md).

The pending generated Sound6-to7 copy adds one9-byte00000000c078000005 reference under
selector6, without duplicating the backing buffer. Both decoded windows are identical,
and the builder independently reproduces the earlier physical owner3 Sound4-to5 copy
exactly. Exact recapture and audible comparison are required before studying deletion
of this shared owner (sound6-to7-generated-copy-control.md).

## Generated owner5 sharing accepted; physical deletion models registered

The Sound6-to7 generated reference now matches an exact952-checksum hardware recapture,
bodyc90ffd7e... Owner5's full Sound6 buffer is unchanged and only Sound6/7 refer to it.
The Sound7 reference is exactly0/30912/owner5; all other sounds/patterns/plain packets
remain intact. Both preview WAVs are byte-identical and user audible checks pass
(sound6-to7-generated-copy-results.md).

The next physical deletion of Sound6 retains Sound7. Full transfer predicts an empty
selector5 and the complete buffer reowned under selector6, header0/30912/owner6,
951 packets/end190215/body15122b45... Retaining owner5 backing storage and the old
Sound7 reference is evaluated as an alternative. Used-window preservation, every
tail code and unrelated-record preservation are independent checks. Unknown layouts
are reported without guessed resolution; no deletion writer is enabled
(shared-sound6-deletion-control.md).

## Shared-owner deletion transfers all data; last-owner removal remains pending

The physical Sound6 deletion matches951 checksums and full model body15122b45...
Sound6/selector5 is empty, and Sound7/selector6 owns all32768 old codes under owner6,
with0/30912 preserved. Every used/tail code and all unrelated records/patterns remain
exact. Retained owner5 storage/reference alternatives fail. The user reports completion;
audible checks are not separately confirmed (shared-sound6-deletion-results.md).

Only Sound7 now refers to owner6. Its next deletion separately tests actual record
removal versus retained full backing codes. Clearing selector6 predicts815 packets/
end156758/body12acce04..., which also equals the independent genuine pre-creation
hardware backup. No generated deletion writer is enabled (unshared-sound7-deletion-control.md).
The verified Sound6-to7 copy alone is promoted into bounded edit plans; its compiled
WAV exactly replays the earlier hardware-accepted file (edit-plans.md).

## Final-owner removal recovers the prior state; odd-page capacity remains pending

Physical Sound7 deletion now removes all136 data packets/32768 codes.815 checksums
pass, Sound6/7 are empty, and full body12acce04... equals the independent pre-creation
hardware state. All unrelated records/patterns remain exact; retaining owner6 data
fails (unshared-sound7-deletion-results.md). Physical RAM reclamation is not measured.

Both known deletion cases are bounded edit-plan operations; a full copy/transfer/
removal sequence replays genuine intermediate bodies and a previously accepted WAV.
No Sound6/7 pattern events or unknown referrer/layout contexts are allowed.

The next capacity probe supplies an extra unused4096-code page under Sound6, changing
capacity32768 to36864 while retaining the whole original record/window. Exact nine
pages, rounding and unused-page removal are independent outcomes; neither physical
allocation units nor universal endpoint/capacity rounding is inferred in advance
(sound6-nine-page-control.md).

## Nine serialized pages accepted; smaller-buffer WAV import pending

The nine-page candidate now exactly matches968 hardware checksums/body196444b1...
Sound6 retains36864 codes with0/30912/owner5, including the old32768-code prefix and
extra zero page. The used window and every unrelated packet remain exact; rounding
and unused-page removal fail. Audible checks are user-confirmed. This verifies this
serialized capacity, not physical RAM units (sound6-nine-page-results.md).

The next import reads an actual saved100ms48k PCM WAV, resamples125/256 and mu-law
encodes2344 native samples into one4096-code buffer, header0/2344/owner5.832 packets/
end160948/bodyc9ddfcbe... pass software checks. Capacity, endpoint, code-prefix and
used-window preservation are separate outcomes; a failure would not isolate capacity
from the changed endpoint (sound6-one-page-import-control.md).

## One-page WAV import accepted; bounded importer and mono44.1k test available

The real capture passes832 checksums and matches bodyc9ddfcbe... exactly. Sound6 keeps
4096 codes and0/2344/owner5, including all imported2344 frames and zero tail. Other
packets/patterns remain exact and audible checks are user-confirmed. The2344 endpoint
is retained without recording-length alignment (sound6-one-page-import-results.md).

A bounded public importer now supports integer PCM mono/selected stereo44.1/48k,
Sound6 empty/unshared zero-start layouts and only verified capacities/length bounds.
Its100ms replay equals the accepted WAV byte-for-byte. The pending mono44100 chirp
imports17579 native frames into32768 codes,0/17579/owner5, using625/1176 resampling.
Metadata, code prefix, window and exact-body preservation are separate checks
(sample-import.md; sound6-mono-WAV-import-control.md). Other source pairs, shared
replacement and general allocation remain unsupported.

## Mono WAV import accepted; copy of imported endpoint pending

The mono 44.1 kHz PCM chirp imported by the public command exactly matches the genuine
951-packet recapture. Sound6 preserves 32,768 codes, the zero-start/self-owner5 header,
endpoint 17,579, all imported codes and all unrelated packets/patterns. The user confirmed
the audible checks. This verifies this source/state, not arbitrary lengths or memory
limits (sound6-mono-WAV-import-results.md).

The next isolated Sound6-to7 copy inserts the imported header as a nine-byte reference,
without adding backing storage. It predicts 952 packets/end190229 and unchanged owner5
codes. Exact reference endpoint and whole-body equality are separate checks; existing
public lifecycle guards remain narrower (imported-sound6-to7-copy-control.md).

## Imported endpoint reference copy verified

The Sound6-to7 copy retains the exact nine-byte 0/17579/owner5 reference, every original
32,768-code backing byte and all unrelated packets/patterns. All 952 checksums and the
entire target body match; the user confirmed matching sweeps. Public reference copying
now supports the two verified endpoints 17,579 and 30,912 in its existing narrow slot
and ownership context (imported-sound6-to7-copy-results.md).

The next physical Sound6 deletion predicts clearing selector5, moving the complete
buffer to self-owner6 under Sound7, and preserving endpoint 17,579. Retained/dangling
owner alternatives and loss of unused tail codes are independent checks. This does
not extend deletion guards in advance (imported-shared-sound6-deletion-control.md).

## Imported shared deletion transfers every backing code

The physical capture exactly matches the 951-packet model 684437bc.... Sound6 clears;
Sound7 becomes a full self-owner6 record with unchanged endpoint 17,579 and all 32,768
codes, including the unused tail. Other records and patterns remain exact, and the user
confirmed the audible checks. Shared Sound6 deletion now supports this endpoint within
its existing guards (imported-shared-sound6-deletion-results.md).

The next unshared Sound7 deletion predicts removal of its entire record and return to
body12acce04..., independently observed in the earlier last-owner control. Empty-record
and retained-backing alternatives remain separate hypotheses; physical RAM reclamation
is not inferred (imported-unshared-sound7-deletion-control.md).

## Imported last-owner removal completes the lifecycle; tempo candidate pending

Final Sound7 removal matches 815 checksums and the complete independently genuine
body12acce04.... Sound6/7 are empty; every unrelated record and pattern remains exact.
The user confirmed the checks. Both bounded deletion contexts now include endpoint
17,579, and the composed copy/transfer/removal plan replays a previously accepted WAV
byte-for-byte (imported-unshared-sound7-deletion-results.md).

The next control isolates one BPM preset press without touching knobs. Before collection,
the second opaque 7d5c packet's byte129 contains120 within a mostly-zero prefix. Direct
integer BPM at that offset is a preregistered lead, not a confirmed field; the display
values must be observed independently. An unchanged backup remains an eligible outcome,
and all other byte changes are reported without refitting (tempo-preset-control.md).

## First direct tempo-byte association supported; third value and return pending

The independently reported display transition120 to140 corresponds exactly to byte129
in the second7d5c payload changing120 to140. All815 checksums, packet shapes, sample
records, patterns and unrelated bytes remain valid/exact. This supports the preregistered
candidate for one physical transition, not writable-field verification or an arbitrary
BPM range (tempo-120-to140-results.md).

The next two captures preregister140 to80 and80 to120 at the same fixed byte. Exact
whole-body restoration to the independent original120 capture is a separate return
hypothesis. Missing display observations or extra global changes cannot be hidden by
candidate matching. No tempo writer is enabled (tempo-preset-series-control.md).

## Three preset values and exact return support the tempo byte

The independently confirmed140 to80 and80 to120 captures each change only byte129
in the second7d5c payload. Both815-checksum frames preserve every sample, pattern and
unrelated byte. The80 body matches its preregistered prediction; the120 return equals
the complete independent original body. Combined with120 to140, three physical preset
values support the direct integer BPM mapping without offset fitting
(tempo-preset-series-results.md).

The first generated120-to80 candidate already equals the genuine80 native body and
passes full-phase/packet/body waveform roundtrip. Hardware restore and its independent
display reading remain pending. No writable tempo field or arbitrary range is promoted
in advance (generated-tempo80-control.md).

## Tempo preset byte is writable in the recognized context

The generated 120-to-80 restore passes all 815 native checksums and matches the entire
independent genuine 80 body. The user confirmed display80 and the slower unchanged
phrase/samples. Payload byte129 of the second 7d5c record is now writable for the three
observed presets within guards that preserve every other global byte and all unrelated
packets. A public edit-plan replay equals the accepted WAV byte-for-byte
(generated-tempo80-results.md; tempo-preset-edits.md).

Fine tempo remains a separate hypothesis. The next physical 80-to-100 control moves
only knob B while BPM is held and predicts only the same byte changing to100, with
all sample parameters and unrelated fields preserved. The public preset setter still
rejects100 as either source or target (fine-tempo100-control.md).

## Physical fine100 uses the preset byte without collateral parameters

The user reported100 after BPM-held knob B adjustment. All815 checksums and the entire
preregistered bodyd01d2cdd... match. Only second7d5c payload byte129 changes80 to100;
every other global, slot-parameter, sample and pattern byte remains exact. This adds
one non-preset physical value, not a general writable range (fine-tempo100-results.md).

Three next captures preregister100 to60,60 to240 and240 to100 at the same fixed byte.
Each actual state and numeric display reading is checked separately, and the return
must equal the complete independent100 body. Public preset guards remain unchanged;
generated arbitrary fine tempo is still a later gate (fine-tempo-range-series-control.md).

## Fine limits60/240 and exact100 return support the direct unsigned byte

All three independently confirmed captures pass815 checksums and match their fixed-byte
predictions. Second7d5c payload byte129 changes100 to60,60 to240 and240 to100. Every
other global, sound parameter, sample and pattern remains exact. The return recovers
the entire independently genuine original100 state (fine-tempo-range-series-results.md).

The next generated100-to137 probe is an unobserved fine target. Its model reconstructs
both complete physical endpoint bodies, and the137 WAV preserves all native packets
and phase labels in software. Device display/receive/recapture evidence remains pending;
public preset scope is unchanged (generated-fine-tempo137-control.md).

## Fine137 restore verifies integer tempo; swing location remains pending

The generated100-to137 capture passes815 checksums and complete target equality, with
user confirmation of the requested137 display and checks. Every unrelated byte is exact.
Integer60-to240 editing is supported in recognized global contexts using endpoint,
representative-value and generated80/137 evidence, not individual tests of every value.
A public plan replays the accepted WAV (generated-fine-tempo137-results.md; tempo-edits.md).

The next maximum-swing control fixes137 BPM and preregisters byte130 only as a location
lead. Baseline0 is not an observed percentage; units and maximum encoded value remain
unknown. All raw differences/direct-display alternatives are retained. No swing writer
is enabled (swing-max-control.md).

## Swing maximumS18 matches byte130; scale/minimum remain unresolved

The physical maximum capture passes815 checksums and changes only second7d5c byte130
from0 to18. The user independently reportedS18; tempo129 stays137 and every unrelated
field is exact. This is a first positive location/display association, not a percentage,
signedness or timing-unit claim (swing-max18-results.md).

The next series leaves the minimum unspecified, requests displayed9 and returns toS18.
Raw unsigned and signed8 interpretations are declared before collection, not fitted
later. The return must equal the complete independentS18 body; a displayed minimum0
must conditionally recover the independent original zero-byte state. No swing writer
is promoted in advance (swing-range-series-control.md).

## Physical swing display range 0 to 18

Independent S00, S09 and S18 display reports match raw byte 130 values 0, 9 and 18.
Only that byte changes; tempo 137 and all unrelated packets remain exact. Both complete
endpoint returns and the preregistered middle body pass. This supports the fixed
location and positive display mapping; it does not establish percent or clock units,
signedness outside the positive range, or every interior value (swing-range-results.md).

A research timing pair at 0 and new interior value 6 adds the same copied Sound 3/key 16
event at Pattern 1 Step 2. The pair differs only in byte 130. Independent recaptures
and ordinary playback will check stored state and offbeat timing separately.
Public swing editing remains disabled (swing-timing-pair-control.md).

## Generated straight swing with a measured offbeat reference

The swing-0 target restores successfully and recaptures exactly, including the cloned
Sound 3/key 16 event at Step 2. The user confirms the added note is audible. Stored
swing is 0 and tempo is 137; no independent swing display was reported. Ordinary
playback gives 14 complete repeated-tone cycles, with gaps matching 5/16 and 11/16
of the whole loop. The measured repeated component is near 500 Hz, correcting the
initial high-note description. A separate baseline-selected measurement registration
fixes the tone band before swing-6 data; the original registration remains immutable.
No positive generated swing or percent/clock units are claimed yet
(swing-straight-control-results.md; swing-timing-pair-control.md).

## Positive generated swing accepted; two-field global guard enabled

Generated swing 6 recaptures exactly at 137 BPM. All six registered stereo timing
comparisons show the short interval increases about 27 ms, the long interval decreases
about 27 ms and the loop stays steady. The user independently hears more swing; no
independent S06 display reading is claimed (generated-swing6-results.md).

The bounded public setter supports numeric 0 to 18 using physical endpoints/middle
and generated interior evidence, not individual tests of every value. The recognized
global-record hashes now mask only verified tempo byte 129 and swing byte 130.
Unknown other bytes and swing values outside the range still fail. Tempo preserves
swing and swing preserves tempo; units remain unconfirmed. Both accepted timing WAVs
replay byte-for-byte and all 790 regression tests pass (swing-edits.md).

The next joint target sets tempo 100 and swing 9, preserving every sample/event and
all unrelated fields. Software verifies composition and full waveform recovery;
the physical combination remains pending (joint-tempo-swing-control.md).

## Joint tempo/swing composition verified; live sound volume remains open

The new joint 100/9 target accepts on hardware and recaptures exactly. User confirmation
covers the requested100 BPM display and playback checks; the number was not separately
typed, and no swing display is inferred. Only payload offsets 129/130 change. The public
setters reconstruct the genuine body in either order, and inverse137/6 reproduces the
prior complete genuine body (joint-tempo-swing-results.md).

The next stopped/write-off Sound 3 TONE volume probe first captures selection alone,
then knob B at minimum. No volume offset, numeric minimum or serialized effect is
assumed. Global, pattern and sample alternatives and an unchanged body are retained;
audition/display evidence is requested separately. No volume writer is enabled
(sound3-volume-probe-control.md).

## Live volume becomes quieter without a serialized change

Both independent Sound 3 selection/minimum captures exactly match the joint 100/9
body, with 815 valid checksums. The user reports quieter but not silent; no display
number or measured gain is supplied. No sample, pattern or global byte changes under
these stopped/write-off conditions. This supports a live effect without an observed
backup representation in the tested snapshots, not a claim about all volume behavior
(sound3-live-volume-results.md).

The next TONE parameter-lock probe controls plain playback separately, then records
only B movement while holding WRITE. Both primary-only and primary/auxiliary Sound 3
cell changes are alternatives; every other change remains explicit. TONE may snapshot
another live setting, so no volume bitfield, event flag or uniform maximum value is
inferred. No volume writer is enabled (sound3-tone-lock-probe-control.md).

## Recorded TONE associates primary high bits and a low-nibble candidate

Plain playback is unchanged. Recorded B movement changes all 16 Sound 3 primary cells
only: populated `0df883` becomes `cdff83`, previously empty `000000` becomes `c00f00`.
Auxiliary values and all other state bytes remain exact; the user hears louder sound.
First-byte OR0xc0 and second-byte low-nibble replacement0xf exactly reproduce the
observed maximum body as a post-observation model, not a prior bitfield prediction.
High bits remain opaque and new raw empty-cell data is not called a new note
(sound3-tone-lock-up-results.md).

The next minimum/maximum return preregisters only the second-byte low four bits as
a volume candidate. Minimum raw0 is a falsifiable encoded hypothesis; no UI number,
silence or gain unit is assumed. All other bits, including0xc0, must remain exact and
the entire maximum return must equal the independent original loud body. No volume
writer is enabled (sound3-volume-lock-range-control.md).

## Four-bit-only minimum falsified; six-bit and flag alternatives preregistered

Minimum has `0df083` at previously populated Sound 3 cells and `000000` at formerly
empty cells. First-byte0xc0 clears as well as second-byte0x0f, falsifying the narrow
mask. The complete maximum returns exactly to e34fbe7f.... All noncandidate state,
including auxiliary values and globals100/9, remains exact. User reports lower relative
loudness at minimum; no numeric UI/gain/pitch-stability reading is invented
(sound3-volume-lock-range-results.md).

A new post-observation candidate is mask0x0fc0 across the first two primary bytes.
Endpoints fit either six value bits or four bits plus zero/nonzero-enable behavior;
they also do not distinguish value ordering. The next quarter/halfway/max-return
series registers both orderings and the flag alternative before data, retaining the
old failed report. Mechanical bands are auxiliary, not definitive gain or bit-order
proof. No volume writer is enabled (sound3-volume-middle-series-control.md).

## Interior masks preserved; neutral reference21 and nonuniform middle

All three captures preserve bits outside0x0fc0 and restore the exact maximum. Quarter
is uniform21 under both orderings. Middle has contiguous values37,41,44,47 and46 by
step, so the original uniform-middle/band condition fails and remains false. First-byte
pairs01/10 refute the simple nonzero-enable pair. User confirms increasing loudness;
no UI scale,gain curve or pitch stability is inferred (sound3-volume-middle-series-results.md).

The next generated pair independently replays uniform21 and changes only the two masks
to contiguous18/alternate36. Those interpretations predict opposite amplitude directions.
A frozen steady-tone method requires consistent stereo amplitude,pitch and loop timing;
reference data is checked before the candidate. No public volume writer is enabled
(generated-sound3-volume18-control.md).

## Generated lower-interior gain supports contiguous ordering

The genuine21 replay and generated18 restore both recapture their complete target
bodies exactly. In all six frozen ordinary-tone comparisons, candidate amplitude
is approximately0.8189 times reference, while pitch and loop remain stable. This
supports the six contiguous bits6–11 interpretation under mask0x0fc0 in Sound3/P1
primary data and rejects the opposite directional prediction of alternate36.
The user does not reliably confirm relative loudness; recorded audio supplies the
direction. One control does not define a gain law, UI scale, every-value behavior or
general writer. A fixed upper-interior36/alternate9 probe checks the opposite
direction next (generated-sound3-volume18-results.md;
generated-sound3-volume36-control.md).

## Contiguous volume ordering supported in both generated directions

Generated 36 restores exactly and raises the recorded repeated-tone amplitude by
approximately 2.20 times relative to genuine 21, retaining pitch and loop. Together
with the generated 18 decrease, this supports bits 6–11 of the little-endian first
two primary bytes as recorded volume in the tested Sound 3 / Pattern 1 context.
The broader six-bit mask is retained; older failed four-bit and uniform-middle
reports are unchanged. A bounded all-16-cell setter supports raw codes 0..63 only
for the established sample window and note layout, preserving every unrelated bit.
Individual per-step edits, other sounds, a gain law, UI scale and TONE pitch decoding
remain unverified (generated-sound3-volume36-results.md; sound3-volume-edits.md).

## Fresh persistence control precedes recorded TONE pitch

Ordinary playback leaves the complete uniform 36 body unchanged. A new recorded A
probe preregisters first-primary low-six bits as a pitch-location candidate, with
separate pitch-plus-volume and broader Sound 3 primary/auxiliary alternatives. The
existing note cells have candidate value 13 and parameter-only cells have 0; these
are raw observations, not decoded semitones or endpoint predictions. Ramps remain
literal. Public volume guards stay unchanged and reject a changed nonvolume layout
(sound3-volume-post-playback-results.md; sound3-tone-pitch-probe-control.md).

## Recorded pitch down changes only the first-primary candidate

All 16 Sound 3 / Pattern 1 first-low-six fields become raw 1. Existing note tuples
0df983 become 01f983; parameter-only 000900 becomes 010900. All auxiliary values,
volume 36 and unrelated state remain exact. The user hears lower pitch and sees Ptc
with qualitative ticks; no numeric UI value is supplied. Only differing bits 0/2/3
are exercised here, so full field width and semitone units remain unknown. A new
upper/return control compares low-six and low-five masks and predicts the entire
low-end return, preserving broader alternatives (sound3-tone-pitch-minimum-results.md;
sound3-tone-pitch-range-control.md).

## Pitch endpoints fit the low-five mask; generated interval remains pending

The high end has uniform raw 25 and the exact return has uniform raw 1. Only first
primary low-five bits change; bit 5, volume 36 and all other state remain unchanged.
Both low-five/low-six alternatives fit, so full field width remains unknown. The
next fixed 13/14 research pair preserves bit 5 and preregisters a common-search
frequency test before audio. Frequency direction and a one-semitone ratio are
separate hypotheses; no general pitch writer or all-code law is inferred
(sound3-tone-pitch-range-results.md; generated-sound3-pitch-pair-control.md).

## Generated uniform13 is accepted as the interior audio reference

All16 first-low-five candidate fields now contain13 in an exactly accepted generated
body; volume36 and all unrelated state remain unchanged. Ordinary playback fits the
prior repeated-tone lead near500.626 Hz under all six frozen measurements. This
supports the generated reference, including parameter-only cells, without claiming
the candidate14 interval, full field width or a general pitch law. Candidate data
is the next independent step (generated-sound3-pitch-pair-control.md).

## Generated13→14 supports a one-semitone-sized pitch interval

Exact candidate14 reception preserves volume36 and every unrelated bit. Six frozen
ordinary-audio ratios correspond to approximately99.53 cents, supporting the
registered one-semitone interval with stable loop. A bounded uniform raw1..25 pitch
setter changes first-primary bits0..4 only within the tested layout, guarding bit5
and other parameters; no all-code law or complete field width is claimed.
The next FILTER candidate covers second-primary0xf0 and third-primary0x03, with
broader third-byte/primary/auxiliary alternatives and a fresh selection control.
Cutoff and resonance remain opaque hypotheses
(generated-sound3-pitch-interval-results.md; sound3-pitch-edits.md;
sound3-filter-probe-control.md).

## Confirmed FILTER selection preserves the complete current body

The fresh selectionA backup exactly matches the accepted generated14 body and all
packets. Pitch14, volume36 and every unrelated field remain unchanged. This controls
prior ordinary playback plus mode selection with no knob movement. The later
WRITE-held A pass remains a separate masked-location test against actualA, preserving
broader third-byte/primary/auxiliary alternatives without guessing an endpoint or
promoting a filter writer (sound3-filter-probe-control.md).

## FILTER A clockwise isolates the six candidate bits

Only second-primary high-four / third-primary low-two bits change across all16
Sound3/Pattern1 cells. Contiguous projection62 and alternative59 reproduce the raw
data; neither bit order nor scalar/mode interpretation is established. Pitch14,
volume36, auxiliary values, other third-byte bits and all unrelated state remain exact.
The user hears high-pass filtering to inaudibility, without a measured zero or Hz/UI
number. A new counterclockwise/return control preserves the masks and predicts the
whole clockwise return (sound3-filter-A-clockwise-results.md;
sound3-filter-A-range-control.md).

## FILTER A endpoints and exact return retain two bit groupings

The counterclockwise pass has contiguous 1 / alternate 4 in all 16 cells; the
clockwise return has 62 / 59 and exactly reproduces the independent entire body.
Only second-primary high-four and third-primary low-two bits change. Pitch 14,
volume 36, auxiliary values and other third-byte bits remain exact. Reported
inaudible LPF/HPF extremes do not determine encoding order or Hz units. A new center
control tests both monotonic scalar interpretations without guessing a center code;
ordinary playback independently tests near-prior tone-component amplitude
(sound3-filter-A-range-results.md; sound3-filter-A-center-control.md).

## FILTER center 63 fails both numerical between-endpoint hypotheses

All 16 candidate values are literal 63 under both bit groupings, outside both
endpoint intervals. Strict masks, pitch 14, volume 36 and all other state remain
exact; the failure is retained independently of passing native and audio checks.
Six fixed audio comparisons support near-prior repeated-tone amplitude, while
the user reports neutral-like playback and a single middle display tick. A special
neutral code with separate low-pass/high-pass branches is a new post-center
hypothesis, registered before two interior controls and exact center return.
Encoding order, mode bits and broadband bypass are not established
(sound3-filter-A-center-results.md; sound3-filter-A-interior-control.md).

## Interior LPF16/HPF52 supports contiguous branch ordering

Recorded interiors are uniform contiguous 16 / alternate 1 for user-confirmed LPF,
and 52 / 19 for HPF. Both contiguous branch-order hypotheses pass and both alternate
branch predictions fail. All strict masks, pitch 14, volume 36 and noncandidate
state remain exact; the entire center return reproduces the independent 63 body.
This supports a contiguous branch ordering without proving mode bits, complete
width or an all-code Hz law. Fixed generated 16/52 bodies match both independent
captures exactly; generated reception remains pending and no public filter setter
is enabled (sound3-filter-A-interior-results.md; generated-sound3-filter-pair-control.md).

## Generated FILTER16 reception and low-pass listening are verified

The entire generated16 target and every packet recapture exactly, matching the
independent recorded low-pass body. Strict candidate masks preserve pitch 14,
volume 36 and every other bit. User low-pass listening confirmation is separate
from exact native evidence. The prepared generated52 high-pass leg remains
pending; this first acceptance does not promote a general filter law, resonance
field or public setter (generated-sound3-filter16-results.md;
generated-sound3-filter-pair-control.md).

## Generated16/52 acceptance enables only observed-code FILTER editing

Both generated interiors recapture as complete independent bodies and all packets,
with user-confirmed LPF/HPF behavior and every noncandidate state bit exact. Public
uniform Sound3/Pattern1 plans now support literal1/16/52/62/63 only, guarding pitch14,
volume36, keys, sample window and all opaque other bits. No general all-code or Hz
law is promoted. Exact accepted WAV replays and1,025 regression tests pass; the next
public-plan63 target reproduces the independent complete center body before new
hardware data (generated-sound3-filter-pair-results.md; sound3-filter-edits.md;
generated-sound3-filter-center-control.md).

## Public center63 reception is exact; B remains an untested field

The public plan reconstructs the entire independent center body and every packet
on hardware, with user-confirmed unfiltered playback and every unrelated bit
preserved. FILTER B's resonance role is documented, but its storage is now tested
under separate third-primary masks0x7c/0xfc. Bit7, raw five/six-bit projections,
coupled A changes and no-change results remain explicit; no resonance width or
writer is promoted and public cutoff guards stay unchanged
(generated-sound3-filter63-results.md; sound3-filter-B-probe-control.md).

## B minimum exercises bit7; narrower candidate fails

Only third-primary bit7 clears at note steps1/2/5/9/13, making the raw six-bit
projection0 throughout. The narrow five-bit projection was already0. Mask0xfc fits
the changes;0x7c fails and remains retained. All keys, pitch14, volume36, cutoff63
and unrelated state remain exact, with no user-reported audible change. Full width,
lower bits and bit7's general role remain unknown. A new maximum/return control
predicts the entire independent minimum body while retaining broader alternatives
(sound3-filter-B-minimum-results.md; sound3-filter-B-range-control.md).

## B0/63 endpoints fit all third-primary high-six bits

Maximum is uniform six-bit63 / narrow31; the exact minimum return is0 throughout.
All six bits2..7 differ between endpoints, with pitch14, volume36, cutoff63, keys
and every other state bit exact. The user sees resonance adjustment but hears no
change at neutral cutoff. A new fixed LPF16 pair varies only B0/63 between targets,
registering exact reception and a common tone-amplitude hypothesis before audio.
General bit7 semantics, all-code law and a writer remain unconfirmed
(sound3-filter-B-range-results.md; generated-sound3-resonance-pair-control.md).

## Generated cutoff16/B0 combined reference is physically accepted

The entire generated reference and every packet recapture exactly, with all16
cutoff candidates16 and B candidates0. All non-FILTER state remains exact. Frozen
ordinary audio is usable near530.28Hz with stable loop timing, and the user hears
the filtered pattern. The prepared B63 target differs only in third-primary
bits2..7 and remains a new reception/audio test; no general resonance law or public
writer is promoted (generated-sound3-resonance-reference-results.md;
generated-sound3-resonance-pair-control.md).

## Accepted B0/B63 pair has a measured component-amplitude effect

At fixed cutoff16, generated B63 exactly recaptures its target while preserving
all non-B state relative to B0. Six frozen tone comparisons show ratios around7.15,
with frequency and loop consistent. User listening supports a stronger resonance
or filter effect. This supports a functional interpretation of the candidate
block but not every code's law or bit7's full role. A new B32 target tests an
interior value against both already observed endpoint audio sets
(generated-sound3-resonance-pair-results.md; generated-sound3-resonance-middle-control.md).

## Accepted B32 enables only observed-code resonance editing

The entire B32 target recaptures exactly, with frozen component amplitude between
B0/B63 and every non-B state bit preserved. Public uniform edits support only
0/32/63 at cutoff16/pitch14/volume36 with known notes/sample layout and uniform or
specific legacy source states. All three accepted WAVs replay exactly; all1,137
regression tests pass. The next FX7 control tests Pattern1 bytes1024..1031 while
retaining both nibble orders and broader changes, without guessing an effect code
(generated-sound3-resonance-middle-results.md; sound3-resonance-edits.md;
pattern1-FX-probe-control.md).

## FX7 footer6 co-occurs with global byte131=9

Only Pattern1 footer bytes and second0x7d5c payload byte131 change: FF to66 footer,
0 to9 global. Notes, parameters, samples and all remaining state stay exact. The
original footer-only hypothesis fails and is retained; a two-field model is
explicitly post-observation. User listening confirms octave-up, but uniform footer
nibbles do not establish order and the global byte's role is unknown. New FX8/clear
controls test low-four/whole global-byte scopes and independent no-FX return,
without promoting a complete map or writer
(pattern1-FX7-results.md; pattern1-FX8-clear-control.md).

## FX8 footer7 passes; clear input is duplicated

Octave-down has footer7 and global byte131=1, with all other state exact under
the registered low-four scope. The first listening confirmation supports lower
octave. Both supplied raw WAVs are identical, so the alleged clear capture is not
independent and its false footer comparison cannot judge the clearing model.
The unchanged clear prediction now awaits corrected input in a fresh folder;
global meaning and nibble order remain unknown
(pattern1-FX8-results.md; pattern1-FX16-corrected-clear-control.md).

## Corrected FX16 clear returns FF; global131 remains opaque

Independent corrected input verifies footerFF and the original pre-FX state
except global131, now7. Entire original-body equality is false because that byte
was0. The low-four scope passes. Uniform footer6/up,7/down,F/clear evidence does
not establish nibble order or a full effect enum. Ordinary playback is now
registered separately to investigate the global change without FX or write
(pattern1-FX16-corrected-clear-control.md; pattern1-playback-global-control.md).

## Battery replacement and plain playback preserve global131=7

Two distinct captures after reported battery replacement equal the entire clear
body, including global131=7. Normal playback at the observed stop causes no
serialized change. The byte remains opaque. A fixed generated footer6/global7
restore now tests octave-up without reproducing physical FX7's co-occurring
global9; exact target and listening checks stay separate
(pattern1-plain-playback-results.md; generated-pattern1-FX-up-control.md).

## Generated footer6 succeeds with global131 kept at7

Exact physical reception confirms that only the eight footer bytes changed to66,
with global131=7 and all other bytes exact. The user hears the octave effect in
the requested up-test context; no new explicit direction or measured ratio is
supplied. Recorded-up global9 is not needed for this result. The global remains
opaque and uniform footer values still cannot establish per-step nibble order.
A fixed generated footer7/F return pair is registered before new data
(generated-pattern1-FX-up-results.md; generated-pattern1-FX-return-control.md).

## Uniform up/down/clear plans supported; mixed blocks pending

Exact generated down/global7 reception and explicit lower-octave listening pass.
Generated clear/global7 returns the entire independent clear body and normal
playback. Uniform named effect plans now support only none/up/down under an
exact normalized-body context guard. All three accepted WAVs replay exactly.
Old observations retain writer-disabled status at creation. A mixed four66/four77
footer restore is registered before new data; its chronological-half hypothesis
does not resolve adjacent-step nibble order or global meaning
(generated-pattern1-FX-return-results.md; pattern1-effect-edits.md;
generated-pattern1-FX-mixed-control.md).

## Mixed blocks match native target and higher-then-lower listening

The accepted footer6666666677777777/global7 body preserves every other byte;
the user confirms first high then low. Both nibble orders still give identical
halves. New F6/6F first-byte targets clear all remaining effect nibbles and freeze
first-tone frequency alternatives before both physical/audio captures. Public
plans remain uniform-only; general per-step ordering is not yet established
(generated-pattern1-FX-mixed-results.md; pattern1-FX-first-pair-control.md).
