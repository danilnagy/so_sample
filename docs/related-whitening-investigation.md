# Related-device whitening hypothesis

The [libpo32 repository](https://github.com/ericlewis/libpo32) is a newer implementation
for PO-32 acoustic transfers. A read-only checkout is pinned at
`3b3a0a758ba452fc809027c5bafcc5e2d0931532` under ignored reference/libpo32.
Its own LICENSE is MIT, copyright2026 Eric Lewis. Audit hashes are saved in
../experiments/related-whitening-audit-001.json. No upstream program or build was run.

The [pinned source](https://github.com/ericlewis/libpo32/blob/3b3a0a758ba452fc809027c5bafcc5e2d0931532/core/src/po32.c)
implements byte addition of a CRC state's low byte before transmission, and advances
that state with a CRC-CCITT update on the original byte. This is a concrete stateful
model worth testing; PO-33 compatibility is unverified. The research helper expresses
the CRC mathematically with polynomial0x1021 and additive whitening, rather than copying
the upstream implementation. No source from the earlier unlicensed checkouts was copied.

## Finite probe

../experiments/related-whitening-probes-001.json pins the minimal empty-A artifact and
source. Each phase view uses[8500,43000), excluding the repeated acquisition region
and terminal carrier. Every candidate retains its coordinate/packing provenance:

- Raw labels, staggered circular phases and staggered phase increments.
- All24 value permutations,4 within-channel packing offsets.
- Left-only, right-only, alternating stereo symbols and alternating packed channel bytes.
- Packed byte order and reversed byte bits.
- Constant plaintext0 and255; all65536 CRC initial states.

There are2304 enumerated streams, not necessarily independent hypotheses. Three encoded
bytes select candidate initial states; at least13 additional bytes must agree with the
same model for a16-byte run. Multiple initial-state matches are retained. Constant wire
runs are excluded from varied-content evidence. This is a bounded diagnostic, not an
assumption that clearing the device creates all-zero native memory.

237170 three-byte candidates were checked; zero varied16-byte runs validated. This does
not reject every scrambler: plaintext constancy is unverified, independent left/right
mappings and reversed stereo order are untested, and PO-33 may use other framing,
state updates or coding. No payload bytes, checksum or editable fields are established.

Three positive/negative controls pass: constant0 and255 streams made using
standard-library CRC-CCITT with a known hidden seed, corrupted continuation rejection,
and exclusion of constant wire/invalid dtype. Synthetic controls are not device captures.

Reproduce from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/whitening_probes.py experiments/empty-001-a/derived/analysis-001/capture.symbols.npz --out experiments/related-whitening-new.json
```

The [PO-PatchStudio author's current roadmap](https://squarewave.studio/po-patchstudio)
also describes PO-33 transfer decoding as unresolved. This is a source-author claim,
not independent proof that no other implementation exists. (Later note, 2026-11-10: the
roadmap is out of date; libpo32, since renamed [libpo](https://github.com/ericlewis/libpo),
added PO-33 support independently in November 2026. See [prior art](prior-art.md).) No PO-32 tool is treated as
a PO-33 editor or run against the user's device.

## Subsequent coverage and successful interpretation

Additional raw circular-increment and coordinate-XOR views still yield no match in the
earlier left-first layouts, at both16-byte and8-byte thresholds. Those failures remain
in related-whitening-probes-002/003.json. Five separate independent-channel/stereo-order
reports then enumerate92,160 streams. The staggered-increment view with mapping(0,3,2,1)
on both channels and **right-first** alternating symbols reveals long valid zero runs.
The offset1/3 candidates differ only by one byte's acquisition position.

Recovering the state and checking whole packet chains identifies initial1D0F at byte4095,
with the same CRC-additive rule. Held-out, registered-source records validate56,090 packet
checks across24 captures. The successful layout was absent from earlier probes; no failed
result was rescued by rewriting arrays. See packet-decoding.md and packet-corpus-002.json.
