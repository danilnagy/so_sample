# Two-kick control and anchor follow-up, round 6

The corrected combined Step 1+Step 2 backup passes capture and waveform checks, but none
of the twelve fixed preregistered predictions matches its shared data. This is a bounded
negative result; state coding remains unresolved. The first upload was the wrong file,
confirmed by the user, and its initial results are marked ineligible.

## Preregistered outcome

../experiments/joint-results-002.json pins the corrected source and checks every predicted
array hash against ../experiments/joint-predictions-001.json. There was no post-capture
fitting, shifting or endpoint correction. The three views are raw labels, staggered
circular phases and their increments; the two operations are XOR and modulo-four addition.
Both channels fail every prediction, by tens/hundreds of thousands of values. The exact
counts, first/last changes and differing lengths remain in the report.

The planned edits use the same kick at two presumed independent steps. Actual state
serialization may include counts, checksums, UI selections or interactions, so the result
does not prove a nonlinear modem/cipher, or exclude all linear encoders of a different
state representation. Sound/step button actions were not separately supplied by the user.
No failed prediction is silently reinterpreted as a successful field mapping.

## Positive structural relationships

The joint versus Step 3-only comparison has last changed phase increment 60010 on both
channels, then identical shared increments to the captured endpoint. In circular-phase
cells, joint minus Step 3 is constant from 60011 onward: 1 left, 2 right modulo four.
This explains their raw-label tail differences without a new payload model. Joint versus
empty instead reaches a constant relationship at cell 938283, with offsets 0 left/1 right.
See framing-probes-003.json and staggered-probes-002.json under experiments.

No coordinate/sign disagreement was found by the independent amplitude-derived clock in
the joint capture interior; waveform-probes-006.json records exact sample windows and
acquisition exclusions. Earlier five-capture waveform validation remains unchanged.

## Exact-anchor follow-up

The earlier anchor tests used raw phase coordinates. After the reversible regrouping,
constant rotations vanish from increments, permitting a new exact search in their binary
coordinates. Report: ../experiments/increment-anchors-001.json. This is explicitly
post-observation analysis, not a registered prediction.

There are 32 chosen source positions, including 10000 and 500000 where initial probes
found matches, plus a fixed grid and a late control position. Across two channels and
four variants this gives 256 probes. Every anchor is 256 binary coordinates (128
increments). Searches cover arbitrary bit offsets by packing eight target offsets;
the first eight matches and overflow status are retained. Original source uniqueness is
checked with the same search. Matching anchors extend up to 4096 coordinates on each
side, stopping at a mismatch; extension limits are explicit.

For source increment position 10000 (coordinate 20000), the joint capture contains one
match at coordinate 85860, displacement +65860. The source anchor is unique in the
tested source stream. Matching extensions are:

| Channel | Source coordinate span | Joint coordinate span | Matching coordinates |
| --- | --- | --- | --- |
| Left | [19545,20594) | [85405,86454) | 1049 |
| Right | [19546,20594) | [85406,86454) | 1048 |

No other grid anchor was both unique in the source and displaced in these comparisons.
Matches for source increment 500000 also appear elsewhere in the source itself, so they
are duplicated-pattern observations rather than unique relocation evidence. Exact short
reuse does not establish whole-stream relocation, compression, a field stride or a safe
cut-and-paste edit. No stored array was shifted to make a comparison pass.

## Next informative control

Another kick position provides less information now than a known periodic sound input.
The next proposed control is a short calibration tone sampled into a confirmed empty
melodic slot (1-8), keeping the two-kick pattern and other controls unchanged. We need
the user to identify an empty slot before giving device instructions. No occupied slot
is selected or overwritten based on an assumption.

An ordinary stereo 375 Hz, 2-second PCM16 tone has been prepared at
../experiments/calibration-source-001/tone-375hz.wav, with 50 ms fades and peak 0.25.
Its metadata and hash are alongside it. This is sample audio, not restore data, and
has not been played or sent to the device. A periodic input can test body repetition;
it cannot itself prove the internal codec or sample rate. The capture protocol depends
on the confirmed slot and available memory.

The user subsequently confirmed melodic slot 8 is empty. The requested recording is now
../experiments/event-006-b-tone/capture.wav after sampling the ordinary tone into slot 8,
retaining the two-kick pattern. That folder has complete line-input sampling instructions,
a memory-full stop condition and the explicit reused corrected joint baseline. No fresh
A or A-return is requested.

Four new focused checks passed: arbitrary-bit anchor matching, ambiguity/padding handling,
known extension boundaries and corrected genuine-capture content with the observed Step 3
increment suffix. Ruff checks pass. The last full suite was 134 tests before this addition.
