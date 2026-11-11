# Step 3 experiment: verified return control

Fresh A was skipped at the user's request. The verified empty baseline event-002-a is
reused; the returned A now matches that baseline exactly: 1,970,367 labels on both channels, zero changes or tails, with no alignment.

Recording levels remain suitable, with no clipping. At threshold 0.0063, B has 1,970,367
left and 1,970,366 right labels. Compared with reused A, first changes are 9502 left and
9500 right. The exact preregistered 9501 prediction failed; no alignment was applied.

The containing packed-label byte is 2375 on both channels, after Step 1 byte 2327 and
Step 2 byte 2351. A 24-byte-per-channel spacing is a new coarser hypothesis based on
these observations, not a confirmed state-field size or writable location.

The left differs in 1,471,877 positions and right in 1,471,744; changes extend through
most of the transport. These broad effects still require coding analysis. Source files
are untouched. Exact provisional comparison is in event-003-b/comparison-summary.json.

## Completed control

The returned empty recording is valid stereo PCM with no clipping and the established
recording level. Hash b2abdd86ddad17ef50fa236fe0f97158a1cac5e0dcb2e38845774e7968198e8c.
Its complete streams match the reused empty baseline, closing the missing fresh-A control
with an explicitly documented limitation: no new pre-edit A was collected in this series.

Across three event positions, empty state is reproducible and first changed packed-label
bytes follow 2327, 2351, 2375 per channel. The exact symbol prediction for Step 3 failed
and remains labeled failed. Coarser 24-byte spacing is an observed transport association,
not an editable field offset. We now have controlled data for software investigation of
transport coding before requiring further device recordings or attempting state edits.
