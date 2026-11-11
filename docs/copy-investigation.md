# Stored-sound copy control, round10

Copying Sound8 into Sound1 adds21 complete labels per channel and exposes a large exact
displaced region. This is the first minimal-state control that demonstrates extensive
reused transport content without a new ADC recording. Payload decoding remains unresolved.

The current capture and Sound8-only references are pinned in copy-structure-001.json.
Source details and waveform/endpoint limits are in
../experiments/empty-001-c-copy-to-1/validation.md. All original WAVs are preserved.

## Content evidence

Source Sound8-only has178847 complete labels per channel; copied state has178868.
First strict difference is43270 on both channels. One hundred thousand changed raw labels
at fixed offsets do not mean the stored sound changed: the copy shifted a reusable region.

Exact source increment span[76819,177169) corresponds to copied span[76735,177085):
100350 equal increments per channel, displacement-84. The region contains all four values,
and phase offset is0, so it is not a constant carrier suffix. Strict original comparisons
remain alongside offset diagnostics. The offset search tests-128..128 beyond50000; source
anchors50000/60000 lack matches, while100000/150000/170000 identify the shared region.
Source uniqueness, target ambiguity and exact bit extensions are recorded independently.

This supports reused transmitted content under the device copy operation, while leaving
physical storage ownership and native sound format unverified. A writer may use references,
shared allocation, compression or another representation. No native PCM sample boundary
or writable memory pointer is inferred. The leading portion still needs interpretation.

Reproduction:

```powershell
.\.venv\Scripts\python.exe scripts/copy_structure.py experiments/empty-001-b-tone/derived/analysis-001/capture.symbols.npz experiments/empty-001-c-copy-to-1/derived/analysis-001/capture.symbols.npz --out experiments/copy-new.json
```

## Registered independent destination control

The earlier Sound8 recording first diverged from empty at43354. Sound1 copy diverges
from Sound8-only at43270, a difference84 across seven slot positions. A12-label per-slot
spacing is therefore a candidate, not a confirmed record size; operation types and
before-states differ. In one speculative packed stereo layout this would be6 bytes,
but no corresponding payload layout is verified.

Next copy the existing source8 into empty destination2, retaining1 and8. Keeping the
first populated slot1 unchanged distinguishes front-table slot information from entries
following inline content, without re-recording the sound. The [official copy-sound
operation](https://teenage.engineering/guides/po-33/en) is used; full instructions are in
../experiments/empty-001-d-copy-to-2/README.md.

Before receiving that capture, second-copy-predictions-001.json pins:

- A front-table candidate: first raw difference in[43278,43287), around the proposed next
 12-value slot position.
- An inline candidate: first raw difference in[177085,177121), immediately following the
 current shared region, with an explicit coarse tag/boundary allowance.
- A small metadata-growth candidate: total complete labels178868..178996 inclusive per
 channel, rather than duplicating another full sample.
- Three source anchors per channel at increment positions90000/120000/150000, expected
 unchanged at those same positions. Hashes of their128 uint8 increments are pinned.

These are competing or separable hypotheses, not inferred fields. All chosen windows are
explicitly experimental; failure of both location models remains possible. No alignment,
phase correction, window revision or tail padding will rescue a failed prediction. A
partial endpoint difference and a complete-count failure are reported separately.

The next control requests only one capture and no fresh A/A-return. Source8 and copy1
remain present; select8 after copying to2 so selection does not add a deliberate change.

Three focused checks pass, including independently constructed displaced data, empty
matching spans and the genuine copied-state block. Ruff checks pass. The last full suite
remains144 tests before later research additions; no newer full-suite claim is made.
