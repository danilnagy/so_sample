# Native packet decoding and first controlled trim edit

The PO-33 packet stream is now decoded with validated framing and CRC-additive whitening.
The authoritative corpus, ../experiments/packet-corpus-002.json, verifies56,090 packet
checks across24 registered-source captures, with exact encoded-body re-encoding. Counts
include repeated configurations; they are not independent statistical trials. The corpus
uses the corrected joint upload and previously reviewed high-level baseline profiles.
An earlier corpus row derived from a generated reconstruction is excluded from genuine
source evidence; original reports and artifacts remain unchanged.

## Transport and framing

Use staggered circular phase increments, mapped by `(0,3,2,1)`. Each byte contains two
cells, right two-bit value before left, lowest pair first. Original artifacts, channel
counts and partial terminal intervals are retained unchanged. This is a new wire domain,
not the old packed-absolute-label format.

The observed packet frame begins at wire byte4095 with CRC state0x1D0F. Each packet has
two little-endian tag bytes, one payload-length byte, payload, and a two-byte little-endian
state trailer. Each coded byte is `(raw + low8(state)) mod256`; after each raw byte,
CRC-CCITT0x1021 advances the state. The trailer must equal the state before its emission.
Start tag0x985B and final tag0x826F have empty payloads. Parsing stops only at a validated
final packet. No offsets or seed values are fitted separately for each capture.

The concrete whitening lead came from the MIT-licensed
[pinned libpo32 implementation](https://github.com/ericlewis/libpo32/blob/3b3a0a758ba452fc809027c5bafcc5e2d0931532/core/src/po32.c).
The PO-33 stereo mapping, frame markers and payload structures are local observations.
The implementation uses independent standard-library CRC mathematics and retains the
source attribution. It does not adopt PO-32 tag semantics as PO-33 semantics.

Earlier2304/3840-stream probes genuinely failed within their stated layouts. Five new
independent-mapping/stereo-order probes enumerate92,160 streams. Only the staggered
increment view produces long matching runs; the successful candidates use the same
mapping on both channels but **right-first** stereo order, absent from the earlier search.
Long zero blocks led to a recovered state; the independently documented initial1D0F
and checksum-valid packet chain then validate the interpretation across held-out captures.
Overlapping runs and equivalent packing offsets are not counted as independent discoveries.

## Sample and reference evidence

Sound selector packets0x68B5 carry one zero-based sound/slice id. Sound data0xEF78 follow
their selector in chunks. In the minimal series, the first retained copy owns a65536-byte
sample buffer preceded by a nine-byte header. Other melodic copies have only a nine-byte
reference header. A six-byte selector packet plus a14-byte reference-data packet explains
the observed12/40 transport positions and28-position replacement growth.

At zero start, payload bytes4..7 contain a little-endian value controlled by trim knob B:

| Sound3 capture | Counter |
| --- | ---: |
| Original copy / copy return | 64704 |
| Minimum trim | 79 |
| Maximum trim | 65456 |

The minimum differs from the original in **one plain packet**, index375, whose header
changes from `00000000c0fc000000` to `000000004f00000000`. Recomputing whitening and all
trailers reproduces the captured minimum's encoded body exactly. Rebuilt phase labels
also match both captured channels throughout the required frame span[0,178795).

The header's first four bytes remain zero in these controls, so nonzero-start semantics
and inclusive-end versus length remain unverified. The final header byte links to the
observed backing sound's data; this is not a physical RAM pointer. The writer supports
only the observed zero-start, shared melodic reference and bounded values. Unknown
packets and all sample bytes are preserved.

The sample buffer supports a signed-complement G.711 mu-law interpretation: positive
codes invert all bits before standard decoding; negative codes retain their low seven
bits. At nominal23437.5Hz, the recovered tone measures375.015Hz with99.97% single-sine
explained variance and1.87s audible tone. Ordinary playback measures561.954Hz,1.25s,
consistent with transposition. See ../experiments/sample-codec-calibration-001.json.
Rate is nominal; arbitrary sample types and nonzero-start semantics are not yet tested.

## Usable tools and candidate

Read packets from a reviewed phase artifact:

```powershell
.\.venv\Scripts\python.exe -m po33_re decode-packets experiments/empty-001-h-sound3-copy-return/derived/analysis-001/capture.symbols.npz --out packet-report.json --body-out frame.body.bin
```

The body file contains encoded, framed wire bytes; it is not a complete state image.
Malformed markers, truncated packets and checksum mismatches fail closed. The earlier
noisy default-threshold baseline artifacts remain untouched and must not be substituted
for the reviewed higher-threshold profiles used in the corpus.

The new candidate in ../experiments/generated-sound3-short-001 changes only Sound3's
counter from64704 to8000. It leaves all other plain packets and all sample data unchanged.
Both the unedited control and edited WAV pass strict full-label/count software roundtrip
and recover the exact expected packet bodies with all511 checksums valid. The generated
stream preserves the captured pre-frame phases and appends a new128-cell constant carrier
after the verified final packet. Source captures and their partial endings are preserved;
no raw capture is trimmed or padded to bypass encoder limitations.

The edited WAV SHA-256 is
`1381f7e4576adb14de3074b12101fdf91156b73cd6045e61a632eb0a0ea36053`.
Software validation is ../experiments/generated-sound3-short-001/software-validation.json.
The user reports successful edited restore and the requested short/long tone checks.
The post-test backup's complete native body equals the generated target, with all511
checksums valid, Sound3 counter8000 and unchanged sample bytes. See
[hardware validation](../experiments/edited-trim-001/hardware-validation.json) and
[the completed restore test](native-trim-restore-test.md). The generated unedited control
was not separately tested on hardware. Captured post-frame carrier counts are retained
and are not forced to equal the candidate's canonical ending.

The full suite passes **244 tests in69.17s**. Tests include independently computed bitwise
CRC/trailers, corruption/truncation rejection, hand-calculated mu-law values, exact
reproduction of the genuine minimum trim and source-artifact immutability. Ruff passes.
This is the first hardware-validated controlled native edit; a general sample/pattern
editor is not yet implemented.

## Experimental fixed-size sample writer

The sample module now quantizes normalized mono audio to the nearest signed-complement
mu-law level, using code0 for silence and preserving gain. A narrow writer replaces an
existing zero-start melodic owner's buffer with exactly the same number of codes; all
headers, packet lengths, selectors and unrelated payloads are preserved. Copies pointing
to that owner share the replacement. It performs no allocation or resizing.

The next candidate imports a saved48k PCM750Hz tone, resamples to nominal23437.5Hz,
encodes46875 samples, and pads the existing65536-code backing buffer with18661 zeros.
Software quantization SNR is37.52dB. All trim counters remain as in the verified short
Sound3 state. Strict phase/count roundtrip and all511 packet checks pass. The sample
encoder has now passed its separate hardware test: the new recapture matches the complete
generated body and all backing codes exactly, with all511 checksums valid and unchanged
headers and counters. User completion and the protocol comparison are recorded in
[sample hardware validation](../experiments/edited-sample-001/hardware-validation.json).
Exact acoustic observations were not supplied. See
[completed sample restore test](native-sample-restore-test.md).

## Raw pattern inspection

`inspect-patterns` reports the observed1032-byte payload per pattern, retaining raw
primary rows, auxiliary rows and footer values. It does not decode sound/note bitfields.
The controlled kicks establish a48-byte primary step stride and16-byte auxiliary stride.
Retrospective opaque-byte reconstruction reproduces the genuine Step3 and corrected joint
packet bodies exactly. The Step2-only auxiliary byte differs by one and remains unresolved.
See [native pattern controls](native-pattern-results.md). The first generated pattern restore
and expected playback are user confirmed; its native recapture comparison now matches exactly.
The [melodic control](melodic-step1-control.md) used the verified empty baseline.

The melodic control is now complete: exactly bytes6/7/8 and770 of Pattern1 change,
supporting three primary bytes and one auxiliary byte per sound slot for Sounds3/9.
No packed note-field meanings are assigned. The experimental `clone-step` command copies
the complete opaque source rows into empty target steps and preserves all unrelated data.
It reproduces the genuine corrected joint kick body exactly. The first four-note
melodic candidate passes full software roundtrip, and the user confirms its restore and
expected playback worked. The after-playback recapture matches the complete generated
body exactly, with all511 checksums valid and unchanged samples and other patterns.
This validates opaque step copies locally, while note bitfields remain under investigation.
See [melodic results](melodic-step1-results.md) and
[pattern restore test](native-pattern-restore-test.md).
The next control [changes keyboard key1 to key2 at a fixed step](melodic-key2-control.md),
with raw-byte hypotheses registered separately from the preservation checks.

That key2 control now passes both preservation checks and registered hypotheses:
only Pattern1 byte834 changes F0→F1, with primary0df883 and all other data preserved.
The low-nibble keyboard-index mapping is supported for Sound3 keys1/2 only. The new
`set-note-key` writer is restricted to those known keys and source-cell parameters,
and reproduces the genuine forward/inverse packet bodies exactly. Its first generated
alternating-key candidate changes only Step13's auxiliary byte962 and passes full
software roundtrip. See [key2 results](melodic-key2-results.md) and
[generated key restore test](native-note-key-restore-test.md). Hardware acceptance of
this field edit is now user confirmed and its recapture matches exactly. A left-channel
timing slip in the original crossing decode is preserved; measured-clock recovery passes
all511 checksums without target data or packet repair. That same method matches all24
existing corpus bodies. See [measured-clock recovery](measured-clock-recovery.md).
Key1/2 field writing is validated locally; the next registered control tests
[the far keyboard endpoint](melodic-key16-control.md).

That endpoint now passes both control invariants and hypotheses: key16 changes only
auxiliary834 F1→FF, with primary0df883 and all unrelated packets preserved. Measured-clock
decoding resolves another archived crossing failure, validating all511 packets.
Sound3 indices0/1/15 are physically observed; middle values and generated key16 behavior
are still untested. The writer remains bounded to keys1/2. The next independently
registered control is [keyboard key7](melodic-key7-control.md).

The independent key7 control now fits: only auxiliary834 changes FF→F6, with primary
and all unrelated state preserved. The writer now supports the four directly calibrated
Sound3 keys1/2/7/16, requiring known source parameters and rejecting other keys or sounds.
It reproduces the genuine endpoint and middle control bodies and inverses exactly.
The first generated four-key phrase now passes its separate
[hardware restore test](native-four-keys-restore-test.md): the user confirms the manual
pitch comparison, and its genuine recapture matches the entire generated frame with
511 valid checksums and unchanged unrelated state. The initial crossing failure at
wire byte 9941 is retained; measured-clock recovery again succeeds without target data
or packet repair. See [four-key results](native-four-keys-results.md). The next
[Sound 2 addition control](sound2-layer-control.md) tests another sound cell alongside
an existing note. A complete keyboard range and other note parameter meanings are not claimed.

The Sound 2 control passes all preservation checks and supports a second cell on
Step 1. Its primary0d2831 differs from predicted Sound 3 primary0df883; that
hypothesis is rejected, while auxiliaryF0 and packet indices4/7 match. See
[Sound 2 results](sound2-layer-results.md). Experimental `clone-sound-cell` copies
the actual parameters intact, retaining a calibrated Sound 3 neighbour and rejecting
occupied or unknown targets. The candidate adds Sound 2 at Step 9, preserving Sound 3
key7 there. Software checks pass; the [hardware test](native-sound-cell-restore-test.md) is pending.

That cell-copy hardware test now passes: the normal decoder recovers the entire generated
4362aa66... frame exactly, with all 511 checksums and unchanged unrelated state. The user
confirms the light and playback checks. See [cell-copy results](native-sound-cell-results.md).
The next bounded operation clears an observed Sound 2 cell while preserving its neighbour.
Software inverses reproduce the complete genuine control and four-key baseline bodies.
The [generated removal test](native-sound-cell-removal-test.md) clears Step 1 only,
preserving the remaining Sound 2 note at Step 9 and all Sound 3 notes; its own hardware
acceptance is pending.

The removal hardware test now passes: the genuine recapture matches the entire
1e493f14... target with all 511 checksums, unchanged neighbouring and remaining cells,
and preserved samples. The user confirms the light/playback checks. See
[removal results](native-sound-cell-removal-results.md). A [read-only project export](project-export.md)
now retains all native packets and source files while exposing pattern JSON and supported
sample previews. The next [sample-start control](sound3-start-control.md) investigates
the nonzero first reference field and alternative second-field semantics without
enabling a nonzero-start writer.

The start control now passes: only the Sound 3 reference changes, with first31393
and second65535. The user still hears the tone. Both second-field predictions fail,
and no nonzero-start semantics are enabled. The raw project preserves this layout
without exporting an unsupported preview. See [start results](sound3-start-results.md).
The next [knob B minimum control](sound3-start-min-control.md) holds start fixed to
distinguish the independently registered second-field alternatives79 and31472.

That fixed-start control passes preservation but yields31504, rejecting both exact
predictions. The subsequent user-reported minimum burst supports a local endpoint
interpretation; no exact minimum-width rule is inferred. See [minimum results](sound3-start-min-results.md).
The bounded `set-sound-end` writer reproduces the whole genuine31504/65535 endpoint
bodies and inverses at fixed start31393. Its first generated interior endpoint39393
candidate passes waveform and packet checks and awaits its own
[hardware test](native-nonzero-trim-restore-test.md). General starts, endpoint inclusivity
and minimum quantization remain unresolved.

That generated fixed-start edit now passes its own hardware comparison: the genuine
recapture equals the complete b3296f2e... target, with all511 checksums valid, and both
requested tone checks are user confirmed. See [window results](native-nonzero-trim-results.md).
Explicit project-export opt-in includes the calibrated preview. The new
[hash-bound edit-plan compiler](edit-plans.md) reproduces the accepted restore WAV byte
for byte while preserving unknown packets and retaining every library guard. The next
[quarter-position start control](sound3-start-quarter-control.md) probes another start;
no general start, minimum-width or inclusive/exclusive endpoint rule is claimed.

That second control passes with start11716/end11827 and511 valid checksums, while both
registered endpoint alternatives fail. Only reference packet375 changes. See
[second-start results](sound3-start-quarter-results.md). The isolated second-start
candidate expands endpoint11827 to19716 and passes strict software waveform/body
roundtrips and inverse reconstruction. Its [hardware test](native-quarter-window-restore-test.md)
is pending; the public endpoint writer and calibrated project previews keep start31393 scope.

The clean second-start retry now verifies the full registered body with511 valid checksums.
See [hardware results](native-quarter-window-results.md). The guarded endpoint/window
writers and explicit previews now accept both discrete observed starts with separate
local bounds; arbitrary starts remain rejected. Window repositioning reproduces both
whole hardware bodies and its edit-plan replay is byte-identical to the accepted WAV.
The next [drum copy control](drum9-copy-control.md) investigates selector8..23 mapping
and slice reference shapes; no drum interpretation is enabled by its registration.

The Sound9 copy now passes with527 valid checksums: sixteen new9-byte EF78 references
appear under selectors8..23, all sharing owner0. Every other native packet and pattern
is unchanged. The Sound9 project view groups the full block rather than interpreting
each selector as another sound slot. See [copy results](drum9-copy-results.md).
Keyboard order and drum previews/writers remain unverified; the next
[key1 minimum control](drum9-key1-trim-min-control.md) isolates one reference.

That control now passes with527 valid checksums: key1 changes selector8 alone, start0
unchanged and second4044→127. The exact79 hypothesis fails and is retained. See
[key1 results](drum9-key1-trim-min-results.md). The project view marks only this keyboard
mapping observed. The experimental endpoint writer is guarded to this exact Sound9/key1
context and local interval127..4044, with genuine forward/inverse whole-body reproduction.
Its first endpoint2000 candidate passes software checks and awaits the
[first drum-edit hardware test](native-drum9-slice-end-restore-test.md).

That first generated drum edit now passes: the entire recapture equals body4eca78dc...
with527 valid checksums, all unrelated state preserved and both tone checks user confirmed.
See [hardware results](native-drum9-slice-end-results.md). A separate explicit export flag
adds only the calibrated Sound9/key1 unpitched preview. The
[next key2 control](drum9-key2-trim-min-control.md) investigates a nonzero-start drum record;
key2 writing and preview remain disabled pending independent evidence.

That independent control now passes: key2 changes selector9 alone, first4045 stays and
second4172 matches the exact registered endpoint prediction. Literal-length127 fails;
the post-capture click is separately user reported. See [key2 results](drum9-key2-trim-min-results.md).
The bounded endpoint writer supports both controlled fixed-start slices and literal
other14 references, with whole genuine forward/inverse body reproduction. The first
key2 endpoint6045 candidate passes software checks and awaits its
[nonzero-start drum hardware test](native-drum9-key2-end-restore-test.md). Project preview
opt-in still includes accepted key1 only; other keys and arbitrary starts remain unsupported.

The clean retry now accepts that generated key2 window: the entire state matches
body1f3295c4... with527 valid checksums, accepted key1 intact and both tones user confirmed.
See [hardware results](native-drum9-key2-end-results.md). The failed first waveform and
analysis remain archived. Explicit project drum-preview opt-in now exports both controlled
keys1/2 under the local guards. The [next Sound10 copy](drum10-copy-control.md) tests an
independent drum-block mapping; Sound10 edits and previews remain disabled in advance.

The clean Sound10 copy now passes all predictions and preservation checks:543 valid
checksums, body9e2801c1..., sixteen new9-byte owner0 records under selectors24..39,
equal to the original Sound9 autocopy. Existing Sound9 edits, samples and patterns are
unchanged. See [copy results](drum10-copy-results.md). Its block is marked observed raw;
individual keys and editing/preview stay unverified. The
[next single-slice copy](cross-drum-slice-copy-control.md) tests Sound10/key1 mapping
and exact source-reference copying without enabling arbitrary drum edits beforehand.

That single-slice control now passes all saved hypotheses and preservation checks with
543 valid checksums and body953e800d... Only packet415/selector24 changes, receiving
Sound9/key1's exact9-byte reference00000000d007000000. This directly maps Sound10/key1;
all other raw packets remain identical. See [results](cross-drum-slice-copy-results.md).
The experimental reference-copy plan retains source windows, owner0/65536 codes and
literal neighboring records. It reproduces both genuine whole bodies and an inverse.
The generated nonzero-start key2 copy awaits a separate
[restore and recapture](native-cross-drum-slice-copy-restore-test.md). Arbitrary mapping,
allocation, Sound10 endpoint editing and audio previews are not enabled.

The generated Sound9/key2 to Sound10/key1 copy now has its own exact hardware recapture:
543 valid checksums, body846092c0..., only packet415 changes from the physical-copy
source, all other state intact and requested tones user confirmed. See
[hardware results](native-cross-drum-slice-copy-results.md). Explicit preview now supports
only Sound10/key1's two accepted copied windows, retaining source/neighbor/buffer guards.
The next [drum-note control](drum10-note-control.md) adds its key1 at Pattern1/Step1,
separating broad row preservation from sound-cell mapping and raw primary/auxiliary
hypotheses. No drum pattern writer or general key encoding is enabled in advance.

That physical note now passes preservation with543 valid checksums/bodyedd7c74f...:
Pattern1 primary[27:30] becomes0df883, auxiliary777 becomes10, only packets4/7 change.
The expected Sound10 cell and Sound3-primary comparison pass; melodicF0 auxiliary and
Sound2-primary comparisons fail. Existing notes and every sample/reference remain intact.
See [results](drum10-note-results.md). A bounded opaque Sound10 copy/removal writer
retains the accepted copied sample and calibrated neighbors, reproducing whole genuine
bodies/inverses. A Step9 copy candidate passes software checks and awaits its
[own hardware test](native-drum-cell-copy-restore-test.md). No general drum key encoding
or primary/auxiliary bitfield semantics are inferred.

The generated Step9 drum-cell copy is now independently accepted: the full recapture
equals body6f4e2cab... with543 valid checksums, only packets5/7 and the four registered
Step9 cell bytes changed from the source. All samples/references and melodic notes
remain intact, with requested grids/playback user confirmed. See
[hardware results](native-drum-cell-copy-results.md). The
[next key2 control](drum10-step9-key2-control.md) tests a recorded replacement in this
same cell, separating preservation from exact auxiliary11/F1 alternatives and primary
retention. Other keys and general nibble meanings remain unverified; note-key evidence
does not independently map Sound10/key2's sample selector.

That recorded key2 control now passes with543 valid checksums/body1ca33191... Only
auxiliary905 changes10 to11, primary0df883 is retained and every other packet is
identical. The exact drum auxiliary prediction passes; melodicF1 fails. See
[results](drum10-step9-key2-results.md). Read-only projection recognizes only the two
observed pairs; sample-reference mapping and generated key2 editing stay unsupported.
The next [Sound4 allocation observation](sound4-allocation-control.md) records a distinct
sample into an empty slot, measuring actual owner/buffer geometry and reporting any
allocator/global changes without assuming length, padding or an allocation rule.

That independent Sound4 recording now passes with679 valid checksums/body523f2dd9...:
only selector3 adds32777 bytes (nine-byte0/28608/owner3 header plus32768 codes) in136
packets. Existing owner0, all other records and every pattern/non-Sound4 packet remain
identical. The sample independently fits1000.033Hz through the existing codec. Its
capacity/tail and endpoint remain distinct; tail bytes are preserved rather than
normalized as zero padding. See [results](sound4-allocation-results.md). The next
[Sound4-to5 copy](sound4-to5-copy-control.md) tests owner3 reference sharing before a
subsequent overwrite/length-change study. General allocation/resizing remains unverified.

That copy now adds exactly one9-byte owner3 reference under selector4:680 valid checksums,
bodyeb19589f..., source buffers/patterns and all non-Sound5 packets intact. The0.0063
acquisition fails the first checksum, as does clock recovery based on it; three fixed
profiles0.004/0.01/0.02 independently recover the identical full native body without
target data or repairs. Analysis003 is the accepted source, and all originals/failed
attempts remain preserved. See [results](sound4-to5-copy-results.md). The next
[shared-owner re-recording](shared-sound4-rerecord-control.md) distinguishes retained
copy content, owner transfer and shared replacement while measuring actual new geometry.

That shared overwrite now passes with985 valid checksums/bodybe92460f... Sound4's
new73728-code buffer uses header0/72128/owner3; Sound5 becomes self-owned owner4 and
retains all32768 old codes and its0/28608 window exactly. Only selectors3/4 change;
all other packet sequences and patterns remain identical. See
[results](shared-sound4-rerecord-results.md). Complete owned buffers follow observed
4096-code page packetization;73728 is not a power of two. No general allocation formula
or writer is inferred. The next [unshared shorter recording](unshared-sound4-shrink-control.md)
tests capacity reduction versus reuse independently of endpoint reduction.

The shorter unshared capture now passes815 checksums/body160983f6... Sound4 capacity
falls73728 to32768, endpoint72128 to30912, with only selector3 changed. All unrelated
plain packets, Sound5's full record and every pattern remain identical. Ordered
4096-code page packetization persists (unshared-sound4-shrink-results.md).

The pending generated growth probe adds170 packets back using the exact device-grown
Sound4 packet geometry, preserving all other packets. Substituting the template's old
codes reproduces its independently captured entire native body. Newly synthesized
codes yield985 packets/end198568 and body5e6946b2..., with strict software WAV roundtrip
equality. This isolated template-based resize is not a general allocator, and hardware
acceptance remains pending (sound4-generated-growth-control.md).

The hardware growth recapture now passes985 checksums and matches the entire generated
body5e6946b2.../plain-packet sequence exactly, including all73728 Sound4 codes and every
unrelated record. Audition checks are user-confirmed; separate hardware acceptance
does not rewrite software evidence (sound4-generated-growth-results.md).

The pending inverse shrink reuses event025's smaller header/136 data-packet geometry
under owner3, yielding815 packets/end156758 and body12acce04... for a new2250Hz sample.
All non-Sound4 packets remain identical. Inverse reconstruction with original template
codes independently reproduces event025's entire body; the synthesized candidate
passes full software WAV roundtrip (sound4-generated-shrink-control.md).

The inverse shrink now matches the complete generated body12acce04... with815 hardware
checksums, all target sample codes intact and all unrelated packets/patterns unchanged
(sound4-generated-shrink-results.md). The next empty Sound6 creation inserts136 data
packets after existing selector5, producing951 packets/end190215 and body258bb81f...
without changing any existing packet. The insertion helper independently reproduces
the full earlier physical empty-Sound4 recording; Sound6 creation remains a pending
hardware probe (sound6-generated-creation-control.md).

The hardware Sound6 creation recapture now passes951 checksums and exactly matches
body258bb81f.../all target packets and sample codes, with unrelated records unchanged
(sound6-generated-creation-results.md). The next generated Sound6-to7 copy adds just
one9-byte owner5 reference and14 encoded-body bytes:952 packets/end190229 and body
c90ffd7e... The source buffer and all unrelated packets remain exact; no memory
capacity is added. Software waveform and independent physical-copy reconstruction
checks pass, but this generated sharing test still needs hardware confirmation
(sound6-to7-generated-copy-control.md).

The generated owner5 reference copy is now hardware-accepted:952 checksums and complete
bodyc90ffd7e.../all target packets match. The full source buffer and every unrelated
record remain unchanged (sound6-to7-generated-copy-results.md). The next physical
Sound6 deletion has a preregistered full-transfer model with951 packets/end190215 and
body15122b45..., preserving every old code under new owner6 and clearing selector5.
Retained-owner and lost-copy outcomes are compared independently, without altering
acquisition or forcing the predicted body (shared-sound6-deletion-control.md).

The actual shared-owner deletion now exactly matches951 checksums/end190215 and
body15122b45... Selector5 becomes empty and selector6 receives every full-buffer code
under self-owner6, with all unrelated packets identical (shared-sound6-deletion-results.md).
The next unshared Sound7 deletion tests dropping its136 data packets:815 packets/
end156758/body12acce04..., independently equal to the earlier hardware shrink backup.
Retained-code and empty-record outcomes remain separate (unshared-sound7-deletion-control.md).

The actual final-owner deletion now drops136 packets/33457 body bytes and matches
815 checksums/end156758/body12acce04..., exactly recovering the earlier hardware state
(unshared-sound7-deletion-results.md). The bounded deletion plan replays both genuine
deletion bodies while preserving opaque packets. The pending capacity probe adds153
data packets under empty selector5: nine ordered4096-code pages,968 packets/end194396,
body196444b1... It retains the original header/codes and adds only one zero page;
device rounding/truncation is compared independently (sound6-nine-page-control.md).

The nine-page recapture now matches968 checksums/end194396/body196444b1... exactly;
all36864 supplied codes and unrelated packets survive (sound6-nine-page-results.md).
The pending ordinary-WAV import shrinks this group from153 to17 packets, following
the observed first-page sixteen255-byte chunks plus25-byte remainder. It sets the
owner endpoint to2344 after actual saved-PCM resampling and preserves every non-Sound6
packet:832 packets/end160948/bodyc9ddfcbe... Capacity and endpoint preservation are
tested independently (sound6-one-page-import-control.md).

The actual one-page import now retains832 checksums/end160948/bodyc9ddfcbe... exactly,
including every code and the unaligned2344 endpoint (sound6-one-page-import-results.md).
The new bounded public importer replays that accepted WAV byte-for-byte. Its pending
mono44100 chirp targets32768 codes/end17579/owner5,951 packets/end190215 and body
5b557a25..., with all non-Sound6 packets preserved (sound6-mono-WAV-import-control.md).

## Public mono WAV import verified

The actual mono import capture decodes at the established threshold 0.0063 into 951
valid-checksum packets and exactly matches native body 5b557a25.... The original CLI
low-threshold attempt remains in analysis-001 and fails its first checksum; the accepted
artifact is analysis-002. No payload guidance or symbol repair was used. All imported,
tail and unrelated bytes remain exact (sound6-mono-WAV-import-results.md).

The imported-sample copy candidate adds one EF78 packet containing the exact nine-byte
owner5 header under selector6. It changes the body length by 14 bytes, predicts 952
packets/end190229 and passes strict full-symbol/full-body software WAV roundtrip.
Hardware acceptance remains pending (imported-sound6-to7-copy-control.md).

## Copying the imported endpoint matches all native packets

The genuine capture passes 952 native checksums at threshold 0.0063 and matches body
0e9ea032... exactly. Sound7 contains only the expected nine-byte reference; all Sound6
codes and every unrelated packet remain exact. A public edit-plan replay reproduces
the hardware-accepted restore WAV byte-for-byte; compiler verification remains software
only (imported-sound6-to7-copy-results.md).

The registered physical deletion prediction preserves source sample page geometry
while moving all codes to owner6 and clearing owner5's selector. It predicts 951 packets,
end190215 and body684437bc.... No generated restore or payload-guided decoding is
needed; the original capture will independently test the model
(imported-shared-sound6-deletion-control.md).

## Imported shared deletion matches the full transfer model

The genuine physical capture passes 951 checksums at threshold 0.0063 and exactly
matches body684437bc.... Only selectors5/6 change: 136 original backing data packets
move to Sound7 with the owner byte changed to6; Sound6 becomes empty and its old
nine-byte Sound7 reference disappears. All code bytes and unrelated packets remain
exact. The public writer and compiled plan reproduce this complete native body
(imported-shared-sound6-deletion-results.md).

The next last-owner prediction removes all 136 Sound7 data packets, yielding 815 packets,
end156758 and the independently genuine body12acce04.... The registered source and
independent matching body are pinned before the new physical capture
(imported-unshared-sound7-deletion-control.md).

## Final imported removal equals an independent native body

The new capture passes 815 native checksums at threshold 0.0063 and equals body12acce04...
from the independent earlier last-owner deletion. It removes 136 Sound7 data packets
and 33,457 encoded body bytes, preserving every unrelated byte. The completed lifecycle
plan's final restore WAV equals the previously accepted Sound4 shrink WAV byte-for-byte
(imported-unshared-sound7-deletion-results.md).

The next tempo control pins both opaque 255-byte global records and preregisters the
second record's byte129 as a direct integer BPM candidate. Valid no-change, other-offset
and multi-byte outcomes remain visible. Numerical evaluation requires the user's actual
before/after display readings; there is no payload-guided decode or tempo writer
(tempo-preset-control.md).

## Tempo changes one plain global byte in the first control

The genuine120-to140 capture decodes at threshold0.0063 into815 valid packets, end156758,
bodye842aaea.... Only native packet index2, tag7d5c, payload offset129 changes120 to140.
Every other plain packet byte is exact. CRC/additive encoding propagates the wire-byte
change; that does not imply changes to subsequent plain sample or pattern data.

The next series pins a predicted80 body2a1a594b... and independent original120 return
body12acce04... before both captures. Native integrity and all raw differences are
checked independently of expected candidate bytes; no symbols are repaired or guided
by the predictions (tempo-120-to140-results.md; tempo-preset-series-control.md).

## Tempo preset series verifies fixed-byte transitions and full return

Both new captures pass815 checksums at threshold0.0063. The second7d5c payload byte129
changes140 to80 and80 to120, with all other plain bytes exact. The80 body2a1a594b... matches
the preregistered prediction; the120 return body12acce04... equals the entire independent
original backup. User display observations are separate and explicit
(tempo-preset-series-results.md).

The generated80 candidate uses the verified packet rebuilder on the genuine120 return.
Its redecoded WAV preserves every phase label and yields exactly the independent80
native body. Capture decoding will remain independent of this target, with all native
checksums required and no expected-byte repairs (generated-tempo80-control.md).

## Generated tempo preset restore equals the independent native state

The new capture decodes at threshold0.0063 into 815 valid packets/end156758 and matches
body2a1a594b... exactly. All plain bytes except the intended tempo byte remain unchanged.
The public hash-bound preset plan replays the accepted restore WAV byte-for-byte;
compiler reports remain unverified by hardware themselves (generated-tempo80-results.md).

The next physical fine-tempo prediction uses the same byte129 with value100 and expected
bodyd01d2cdd.... Extra byte/global/slot-parameter changes remain separately visible, and
decoding uses no expected-data guidance (fine-tempo100-control.md).

## Fine100 control matches all native and preservation predictions

At threshold0.0063, the fine100 recording yields815 valid packets/end156758 and exact
bodyd01d2cdd.... Its only plain change is packet index2, tag7d5c, byte129:80 to100.
The source80 capture and independently reported100 display are pinned separately.
No decoder fitting or expected-symbol repair is used (fine-tempo100-results.md).

The endpoint/return sequence pins bodies8146205d... for60,681d3d77... for240 and the
independent d01d2cdd... for100 before any of its three captures. All other changes remain
visible, including a changed opaque global on a numerically correct return
(fine-tempo-range-series-control.md).

## Fine endpoint series matches native predictions and full original-state return

At threshold0.0063, all three captures yield815 valid packets/end156758. Bodies8146205d...
for60 and681d3d77... for240 match the preregistered predictions; the100 return equals
complete original bodyd01d2cdd.... Only second7d5c payload byte129 changes, with independent
user display confirmation (fine-tempo-range-series-results.md).

The generated137 target body5f25b5ef... is new, not a physical137 capture. Its waveform
passes strict complete phase/native-body/packet roundtrip. Future recapture acquisition
must stay independent of this prediction (generated-fine-tempo137-control.md).

## Generated fine137 recapture equals the new target

At threshold0.0063 the capture yields815 packets/end156758/body5f25b5ef..., matching
the complete137 target. Only second7d5c byte129 changes100 to137; all other plain bytes
remain exact. The public fine-tempo plan replays the accepted WAV byte-for-byte
(generated-fine-tempo137-results.md).

The first swing control pins both global records and leads with byte130, reporting
all other changes independently. No maximum encoding, numeric scale or target-guided
acquisition is assumed (swing-max-control.md).

## Maximum swingS18 changes one independent global byte

At threshold0.0063 the capture yields815 valid packets/end156758/body51b9358a.... Only
second7d5c payload byte130 changes0 to18, matching the reportedS18 numeric component;
tempo137 and every unrelated plain byte remain exact (swing-max18-results.md).

The next series fixes offset130, pins the displayed9 model ea13a17f... and originalS18
return51b9358a..., but guesses no minimum byte or display number. Unsigned/signed8
numeric models are independent alternatives. All differences remain visible without
expected-data decoder repairs (swing-range-series-control.md).

## Swing S00/S09/S18 range and exact returns

All three new captures decode independently at threshold 0.0063 to 815 checksum-valid
packets ending at 156758. Only second `0x7d5c` payload byte 130 changes 18→0→9→18.
The independent display readings match those raw values. Middle body ea13a17f... and
maximum return 51b9358a... match preregistered predictions; minimum 0 exactly recovers
the older zero-swing body 5f25b5ef.... All unrelated bytes remain exact.

Next, two generated research WAVs with the same added offbeat note differ in exactly
one plain payload byte, swing 0 versus 6. Both pass strict phase round trips and exact
body/packet recovery. Hardware recaptures and ordinary timing recordings are pending;
units and public swing writing remain unresolved (swing-range-results.md;
swing-timing-pair-control.md).

## Exact generated straight-control recapture

The generated swing-0/offbeat control independently recaptures at threshold 0.0063
with 815 valid checksums and end byte 156758. Whole native body 1da3b29b... and every
plain packet exactly match the registered target; Sound 3/key 16 was copied to Step 2
and all other samples/events remain exact. Separate ordinary audio verifies the
straight timing baseline. Positive swing-6 device evidence is still pending, and
ordinary playback is analyzed separately from backup demodulation
(swing-straight-control-results.md).

## Positive swing-6 recapture and public replay

The generated swing-6 target independently recaptures at threshold 0.0063 with 815
valid checksums and end byte 156758. Complete body fc595d91... and every plain packet
match. Separate ordinary audio passes all frozen stereo timing hypotheses, with about
27 ms offbeat delay and preserved loop period. No decoding repair or target-dependent
acquisition is used (generated-swing6-results.md).

Public plans reproduce both straight/swing-6 accepted WAVs byte-for-byte. The bounded
tempo/swing guard masks only the two verified bytes and retains strict opaque hashes
elsewhere. The new joint tempo100/swing9 WAV recovers body 1dab085d... in software,
changing only payload offsets 129 and 130; hardware recapture is pending. All 790
regression tests pass (swing-edits.md; joint-tempo-swing-control.md).

## Joint100/swing9 hardware recapture

The joint target independently recaptures at threshold 0.0063 with 815 valid checksums
and end byte 156758. Complete body 1dab085d... and every plain packet match. Only second
global offsets 129/130 changed from 137/6 to 100/9; all unrelated data is exact.
Public setter order is immaterial and the inverse recovers the prior genuine body.
The next selection/volume control reports every raw difference without a candidate
field or assumed minimum; no decoder repair or offset fitting is permitted
(joint-tempo-swing-results.md; sound3-volume-probe-control.md).

## Sound3 live minimum leaves complete project unchanged

At threshold 0.0063 both selectionA and minimumB decode independently to 815 valid
packets ending at 156758. Both complete bodies equal joint100/swing9 body1dab085d...,
with no plain byte difference. The quieter user audition is retained separately and
does not lead to invented gain fields or decoder repairs. Recorded TONE parameters
are the next independent probe, with a fresh plain-playback control and complete raw
cell/packet differences (sound3-live-volume-results.md; sound3-tone-lock-probe-control.md).

## Sound3 recorded TONE changes32 primary bytes only

Both fresh captures decode independently at threshold0.0063 with815 valid checksums
and end156758. PlainA remains body1dab085d.... RecordedB is e34fbe7f..., differing in
the first two primary bytes of all16 Sound3 cells in Pattern1 and nowhere else.
Complete key/auxiliary preservation and non-pattern preservation pass. The literal
post-observation high0xc0/low0xf model reproduces the whole observed body.

Next predictions pin low-nibble-only minimum e8432140... and complete maximum return
e34fbe7f... before collection. No display number, decoder repair or relocated field is
used to rescue a failed model (sound3-tone-lock-up-results.md;
sound3-volume-lock-range-control.md).

## Valid minimum data falsifies narrow mask; exact maximum return

Both new recordings decode independently at threshold0.0063 to815 valid packets and
end156758. Actual minimum4a27f9e1... differs from predicted e8432140... because first
primary high0xc0 bits also clear in all16 Sound3 cells. The low nibbles do reach0.
Maximum return e34fbe7f... exactly matches the entire earlier independent body. The
failed field hypothesis is retained; no decoder repair, new scale or relocated nibble
is fitted into that report. Broader-mask/value-order alternatives are newly registered
for future interior data (sound3-volume-lock-range-results.md;
sound3-volume-middle-series-control.md).

## Interior captures are valid,with a retained middle ramp

All three captures independently decode at threshold0.0063 to815 valid packets and
end156758. Quarter body937b33f0... is uniform21 under both encodings. Middle body0b5673ae...
retains multiple Sound3 values; its uniformity condition fails without data repair or
averaging. Maximum return e34fbe7f... is complete and exact. All noncandidate state is
preserved. New reference21 and candidate18 WAVs recover exact bodies937b33f0... and
f9a66a8a... in software; reception and ordinary gain evidence remain pending
(sound3-volume-middle-series-results.md; generated-sound3-volume18-control.md).

## Generated18 is accepted with exact reception and lower measured tone amplitude

Both pair captures independently decode at threshold0.0063 to815 valid packets.
Reference21 matches body937b33f0..., candidate18 matches bodyf9a66a8a... in full.
Samples, other tracks/patterns, auxiliary keys, globals and noncandidate bits remain
exact. All six original frozen tone measurements give amplitude ratio near0.8189
with stable pitch and loop, supporting the contiguous interpretation. The uncertain
user guess is not used as directional confirmation. A fixed36/alternate9 waveform
recovers bodyc0cc9173... in software and awaits hardware/audio evidence; an earlier
incorrect alternate-code label is preserved as rejected preparation
(generated-sound3-volume18-results.md; generated-sound3-volume36-control.md).

## Complementary volume36 reception is exact

The new recording independently decodes at threshold 0.0063 to 815 valid packets
and complete body c0cc9173..., matching the fixed36 target. All nonvolume bits,
samples and other state remain exact. Frozen audio comparisons support increased
tone amplitude with stable pitch and loop, corroborating contiguous volume ordering
in the tested cells. Public uniform volume plans reconstruct physical 0/18/21/36/63
bodies and replay both accepted interior WAVs exactly. A fresh post-playback capture
checks whole-body persistence before pitch probing
(generated-sound3-volume36-results.md; sound3-volume-edits.md;
sound3-volume-post-playback-control.md).

## Post-playback body remains exact before pitch probing

The new capture independently decodes at threshold 0.0063 to 815 valid packets and
end byte 156758, matching body c0cc9173... and all accepted packets exactly. All 16
raw volume values remain 36. This actual post-playback artifact now anchors the
recorded A probe, which retains no-change, narrow-mask, coupled-volume and broader
Sound 3 alternatives without predicting a target body or repairing data
(sound3-volume-post-playback-results.md; sound3-tone-pitch-probe-control.md).

## Pitch-down data is valid and isolated to the registered candidate

Independent threshold 0.0063 decoding recovers 815 valid packets and end byte 156758.
Body 227d4d25... changes only Sound 3 / Pattern 1 first-low-six candidate bits, with
uniform raw 1 and unchanged volume 36. All samples, globals, other patterns/sounds,
auxiliary values and other bits stay exact. A post-observation uniform1 rule reproduces
the body without becoming a prior endpoint prediction. New maximum data is unknown;
exact minimum return is registered as whole body 227d4d25... before both captures
(sound3-tone-pitch-minimum-results.md; sound3-tone-pitch-range-control.md).

## Pitch maximum and return have valid exact native bodies

Both new captures independently decode at threshold 0.0063 to 815 valid packets and
end byte 156758. Maximum body 3924a9ad... has uniform raw 25; return body 227d4d25...
matches the full independent minimum and all packets. Only first-primary low-five
bits change, with volume 36 and every other state field exact. Fixed generated 13/14
WAVs recover bodies 7f09d458... and 05e1d379... in software; native reception and
ordinary frequency measurements remain pending
(sound3-tone-pitch-range-results.md; generated-sound3-pitch-pair-control.md).

## Generated pitch13 reference reception is exact

The new capture independently decodes at threshold0.0063 to815 valid packets and
complete body7f09d458..., matching every generated target packet. All nonpitch state,
including volume36 and note keys, stays exact. Six frozen ordinary-frequency fits
pass near500.626 Hz with a loop near2.4 seconds. The reference is now physically
verified, while candidate14 reception and its frequency hypothesis remain pending
(generated-sound3-pitch-pair-control.md).

## Generated14 recaptures exactly and supports the registered frequency interval

Independent threshold0.0063 decoding recovers815 valid packets and complete target
body05e1d379.... Frozen ordinary-audio ratios support approximately99.53 cents
for13→14 with loop preserved; all nonpitch state remains exact. Public raw pitch
plans reconstruct independent1/13/14/25 native bodies and both accepted WAVs exactly.
The next FILTER selection control predicts complete body05e1d379... before data;
recorded A waits for that actual baseline (generated-sound3-pitch-interval-results.md;
sound3-pitch-edits.md; sound3-filter-probe-control.md).

## FILTER selectionA recovers the unchanged pitch14 body

Independent threshold0.0063 decoding recovers815 checksum-valid packets and end byte
156758. Entire body05e1d379... and all packets equal the accepted pitch14 project;
there are no payload differences. The actual selection artifact now gates recorded
FILTER A, whose unknown endpoint and competing masks remain as preregistered
(sound3-filter-probe-control.md).

## Recorded FILTER A clockwise has valid isolated native changes

Threshold0.0063 decoding independently recovers815 valid packets and end byte156758.
Body95572be7... changes only the registered candidate masks in Sound3/Pattern1, with
uniform contiguous62/alternate59. All noncandidate state remains exact. A new
counterclockwise endpoint remains unknown, while whole-body return95572be7... is
registered before both captures (sound3-filter-A-clockwise-results.md;
sound3-filter-A-range-control.md).

## Both FILTER endpoint controls have complete native bodies

Independent threshold 0.0063 decoding recovers 815 valid packets and end byte
156758 for each capture. Counterclockwise body 32dd3d1d... has contiguous 1 /
alternate 4; clockwise body 95572be7... matches the entire earlier clockwise body
and all packets at 62 / 59. Only the strict candidate masks change, preserving pitch
14, volume 36 and all other state. The next center backup and ordinary playback are
registered separately, with no guessed interior target body or filter law
(sound3-filter-A-range-results.md; sound3-filter-A-center-control.md).

## Audible FILTER center is a valid body despite scalar-model failure

Threshold 0.0063 decoding recovers 815 valid packets and end byte 156758. Body
8f80a398... has uniform literal 63 under both projections, changing only the strict
candidate masks. All noncandidate state stays exact. Both registered numerical
between-endpoint checks fail and remain in the immutable report; six independent
ordinary-tone comparisons pass their frozen near-prior hypothesis. New interior
branch hypotheses are registered after this failure, with whole body 8f80a398...
and every packet predicted for the final center return
(sound3-filter-A-center-results.md; sound3-filter-A-interior-control.md).

## FILTER interior bodies and exact center return decode independently

All three threshold-0.0063 decodes have 815 valid packets and end byte 156758.
Bodies b5e315b3... (LPF16), fd5c085e... (HPF52) and 8f80a398... (center63) preserve
every noncandidate state bit. The return body and all packets exactly match the
earlier center. The contiguous branch predictions pass while alternate ones fail.
Generated fixed 16/52 WAVs independently recover their complete physical targets;
their new hardware recaptures remain pending
(sound3-filter-A-interior-results.md; generated-sound3-filter-pair-control.md).

## Generated FILTER16 independently recaptures its exact target

Threshold 0.0063 decoding recovers 815 valid packets and end byte 156758, with
complete body b5e315b3... and every packet equal to the registered generated16
target and the independently recorded low-pass backup. All strict preservation
checks pass. A separate user report confirms audible low-pass filtering, allowing
the next unchanged generated52 waveform to proceed to hardware testing
(generated-sound3-filter16-results.md; generated-sound3-filter-pair-control.md).

## Generated52 matches the complete registered high-pass body

Independent threshold0.0063 decoding recovers815 valid packets and end byte156758,
with body fd5c085e... and every packet equal to the generated52 target and earlier
recorded HPF. Pitch14/volume36 and all other state remain exact. Public observed-code
plans replay both accepted16/52 WAVs and prepare a return to full body8f80a398...
for a new generated63 hardware control, without inferring a complete cutoff law
(generated-sound3-filter-pair-results.md; sound3-filter-edits.md;
generated-sound3-filter-center-control.md).

## Public center63 target recaptures before B-field investigation

Independent threshold0.0063 decoding recovers815 valid packets and end byte156758.
Whole body8f80a398... and every packet equal the public-plan63 target and independent
center. Strict masks preserve pitch14/volume36 and all other state. A new recorded
B counterclockwise pass registers unknown endpoint/body and separate0x7c/0xfc
third-byte masks before collection, retaining broader alternatives
(generated-sound3-filter63-results.md; sound3-filter-B-probe-control.md).

## B minimum has valid isolated native changes

Threshold0.0063 decoding recovers815 valid packets and end byte156758. Bodybee177ab...
changes only third-primary bit7 in five Sound3 note cells, preserving all other
state. The0xfc candidate fits;0x7c fails. Both projections become0 throughout, with
no prior endpoint prediction. The next unknown maximum and complete return are
registered before collection, with the entire independent bee177ab... body and
every packet required for return (sound3-filter-B-minimum-results.md;
sound3-filter-B-range-control.md).

## B maximum and exact return have valid complete bodies

Both threshold0.0063 decodes recover815 valid packets and end byte156758.
Maximum bodyfc1ef5b3... has high-six63; return bodybee177ab... matches the complete
independent B0 minimum and all packets. Only0xfc mask bits change. New LPF16/B0 and
LPF16/B63 WAVs recover targets ae37ebfd... and fd0817c1... in software, with new
hardware reception and frozen ordinary-audio evidence pending
(sound3-filter-B-range-results.md; generated-sound3-resonance-pair-control.md).

## Generated LPF16/B0 reference reception is exact

Independent threshold0.0063 decoding recovers815 valid packets and end byte156758.
Complete bodyae37ebfd... and every packet equal the generated cutoff16/B0 target.
All native scope checks pass. Six frozen ordinary-audio measurements are usable
near530.28Hz, enabling the unchanged B63 target to proceed to hardware testing
without changing the registered comparison method
(generated-sound3-resonance-reference-results.md; generated-sound3-resonance-pair-control.md).

## Generated LPF16/B63 reception and frozen amplitude comparison pass

Threshold0.0063 decoding recovers815 valid packets and end byte156758. Whole
bodyfd0817c1... and every packet equal the generated B63 target. Both accepted
pair bodies differ only in third-primary0xfc, with frozen audio ratios near7.15
and stable pitch/loop. A new generated B32 bodyd039d344... is software-verified
before its hardware recapture and two-sided amplitude test
(generated-sound3-resonance-pair-results.md; generated-sound3-resonance-middle-control.md).

## B32 reception and public resonance replay are exact

Threshold0.0063 decoding recovers815 valid packets and end byte156758, with entire
bodyd039d344... and every packet equal to the generated B32 target. Six frozen
two-sided amplitude bounds pass. Public resonance plans reproduce all three
accepted0/32/63 bodies and WAVs. The next saved-FX7 capture has an unknown target,
with footer-only and broader Pattern1 alternatives registered before collection
(generated-sound3-resonance-middle-results.md; sound3-resonance-edits.md;
pattern1-FX-probe-control.md).

## FX7 native body is valid despite footer-only hypothesis failure

Threshold0.0063 decoding recovers815 valid packets and end byte156758. Whole
body99b832a7... is reproduced by footer66 throughout plus global byte131=9, with
all other payload bytes exact. The original strict footer-only result fails and
remains immutable. New FX8 and clear captures are registered under distinct
footer/global alternatives; global values and whole target bodies remain unknown
(pattern1-FX7-results.md; pattern1-FX8-clear-control.md).

## FX8 valid native body and duplicated clear input are separate evidence

Threshold0.0063 decoding recovers815 valid packets and end byte156758. Bodye3a3dfbb...
matches footer77/global1 with every other payload byte exact, passing the first
registered prediction. The two supplied WAVs share the same complete raw hash,
not merely the same native body. Clear therefore remains unverified. Corrected
input uses a fresh artifact/report path and the unchanged original prediction
(pattern1-FX8-results.md; pattern1-FX16-corrected-clear-control.md).

## Corrected clear is independent and checksum-valid

Distinct raw input recovers815 packets ending at156758, body3d3762e2..., with
footerFF and global131=7. The registered clear prediction and every other
pre-FX state byte pass; entire pre-FX body equality is false. Duplicate input
evidence remains unchanged. New plain-playback controls preserve failed narrow
predictions and keep raw-input identity separate from identical native state
(pattern1-FX16-corrected-clear-control.md; pattern1-playback-global-control.md).

## Distinct repeat/playback WAVs share the complete clear native body

Both post-battery-replacement captures recover815 valid packets ending at156758.
Their distinct raw inputs decode to identical body3d3762e2..., with no payload
changes. The next fixed-footer6 restore targets body1147b3d4..., differing only
in eight Pattern1 footer bytes. Its waveform redecodes into every exact target
packet; hardware reception is pending
(pattern1-plain-playback-results.md; generated-pattern1-FX-up-control.md).

## Generated footer6/global7 matches complete physical native target

The independent capture recovers815 valid packets ending at156758, exact
body1147b3d4... with footer66 and unchanged global7. The registered target passes
without masking any global byte. Fixed next targets01cb7130... (footer77/global7)
and3d3762e2... (footerFF/global7) pass generated-waveform native roundtrips;
the second also equals the entire independent clear baseline. Physical down/clear
results are pending; their reports will retain failed exact-target predictions
(generated-pattern1-FX-up-results.md; generated-pattern1-FX-return-control.md).

## Exact down/clear returns and bounded public replay

Both independent captures recover815 valid packets ending at156758. Their
complete bodies01cb7130... and3d3762e2... match the frozen targets without masking
global131. Clear equals the entire independent global7 baseline. Three uniform
public effect plans reproduce all accepted native bodies and WAVs exactly.
A mixed6666666677777777 target is checksum-valid and waveform-roundtripped in
software only; audible chronology remains a new independent prediction
(generated-pattern1-FX-return-results.md; pattern1-effect-edits.md;
generated-pattern1-FX-mixed-control.md).

## Mixed effect body30179809... received exactly

Independent threshold0.0063 decoding yields815 valid packets ending at156758.
The complete mixed target and every packet match, including unchanged global7.
New complementary F6/6F targets differ only in their first footer byte and pass
generated-waveform roundtrips. Their physical capture and first-note audio
results are pending and will not be inferred from native target equality
(generated-pattern1-FX-mixed-results.md; pattern1-FX-first-pair-control.md).
