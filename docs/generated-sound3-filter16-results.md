# Generated low-pass 16 is physically accepted

The new capture independently decodes at threshold 0.0063 to 815 checksum-valid
packets and end byte 156758. Its entire native body and every packet match the
preregistered generated raw-16 target and the independently recorded low-pass
interior. Body SHA-256:
`b5e315b3f0703190ad42652eb57616385e52b2c92df04e3aa2bc1b936c005c37`.
Only the candidate masks differ from the genuine center source; pitch 14, volume
36, keys, sample data and every unrelated state bit remain exact.

The user reports: "done and confirmed I hear low pass filtering". This explicitly
confirms the requested listening check after completing the generated restore
workflow. Exact native reception is separate evidence; the quote is not expanded
into an explicit statement about reception or numeric display readings. No
quantitative cutoff or broadband response was measured.

Capture peaks are approximately 0.1435 and 0.1392 full scale, with no clipping.
The established reduced recording level remains suitable. Current genuine
read-only export: `experiments/exported-sound3-generated-filter16-001/project.json`.
All 31 content hashes and complete native reconstruction pass. Sample previews
retain raw sample codes and do not render the reported filtering.

- [Immutable native reception report](../experiments/edited-sound3-filter16-lowpass-001/hardware-recapture-results-001.json)
- [Separate hardware observation](../experiments/edited-sound3-filter16-lowpass-001/hardware-observation-001.json)
- [User listening report](../experiments/edited-sound3-filter16-lowpass-001/manual-observation.json)
- [Next generated high-pass 52](generated-sound3-filter-pair-control.md)

The first-leg gate now passes. The prepared raw-52 WAV still has its original
registered identity and exact software recovery of the independent high-pass
body; its generated reception and listening remain pending. Existing software
reports stay hardware-unverified. Production code is unchanged, with 88 affected
tests passing in the last focused run and 917 in the last full run. No public
filter writer, all-code cutoff law or resonance field is enabled.
