"""Test a pinned related-device whitening lead against unchanged PO-33 captures."""

import argparse
from itertools import permutations
from pathlib import Path

import numpy as np

from po33_re.analysis.serialization import packed_view
from po33_re.analysis.staggered import CIRCULAR_INDEX, phase_increments, staggered_phases
from po33_re.analysis.whitening import constant_codebook, constant_plaintext_runs
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(path, extra_phase_views=False, minimum_run_bytes=16):
    if type(minimum_run_bytes) is not int or minimum_run_bytes < 4:
        raise ValueError("At least4 bytes required for a continuation check")
    artifact = load_artifact(path)
    report = {
        "analysis_version": "related-device-whitening-0.1",
        "artifact_sha256": sha256_file(path),
        "source_sha256": artifact.metadata["source_sha256"],
        "lead": "https://github.com/ericlewis/libpo32/blob/3b3a0a758ba452fc809027c5bafcc5e2d0931532/core/src/po32.c",
        "window_in_each_phase_view": [8500, 43000],
        "model": "coded=(raw+low8(state)) mod256; state=CRC-CCITT-1021(state,raw)",
        "constant_plaintext_bytes": [0, 255],
        "minimum_run_bytes": minimum_run_bytes,
        "initial_states": "all65536, recovered from first3 coded bytes, remaining>=13 must match",
        "candidate_streams": 0,
        "three_byte_candidates": 0,
        "validated_runs": 0,
        "matches": [],
        "payload_decoded": False,
    }
    if minimum_run_bytes != 16:
        report["analysis_version"] = "related-device-whitening-0.3"
        report["initial_states"] = (
            f"all65536, recovered from first3 coded bytes, remaining>={minimum_run_bytes - 3} must match"
        )
    books = {raw: constant_codebook(raw) for raw in (0, 255)}
    reverse = np.packbits(
        np.unpackbits(np.arange(256, dtype=np.uint8)[:, None], axis=1)[:, ::-1], axis=1
    ).ravel()
    views = [
        ("raw", lambda x: x),
        ("staggered_phase", staggered_phases),
        ("increment", lambda x: phase_increments(staggered_phases(x))),
    ]
    if extra_phase_views:
        if minimum_run_bytes == 16:
            report["analysis_version"] = "related-device-whitening-0.2"
        views.extend(
            [
                ("raw_circular_increment", lambda x: phase_increments(CIRCULAR_INDEX[x])),
                ("raw_coordinate_xor", lambda x: x[1:] ^ x[:-1]),
            ]
        )
        report["extra_phase_views"] = [name for name, _ in views[3:]]
    for name, transform in views:
        pair = [transform(getattr(artifact, ch + "_symbols")) for ch in ("left", "right")]
        if min(map(len, pair)) < 43000:
            raise ValueError("Fixed whitening search requires43000 values per view/channel")
        pair = [x[8500:43000] for x in pair]
        for mapping in permutations(range(4)):
            for offset in range(4):
                for layout in ("left", "right", "stereo_symbols", "stereo_bytes"):
                    data = packed_view(*pair, mapping, offset, layout)
                    for bit_order in ("as_packed", "reversed_byte_bits"):
                        coded = data if bit_order == "as_packed" else reverse[data]
                        report["candidate_streams"] += 1
                        for raw, book in books.items():
                            result = constant_plaintext_runs(
                                coded, raw, book=book, minimum=minimum_run_bytes
                            )
                            report["three_byte_candidates"] += result["three_byte_candidates"]
                            report["validated_runs"] += result["validated_runs"]
                            if result["validated_runs"]:
                                report["matches"].append(
                                    {
                                        "view": name,
                                        "mapping": list(mapping),
                                        "offset": offset,
                                        "layout": layout,
                                        "byte_bit_order": bit_order,
                                        **result,
                                    }
                                )
    report["limits"] = [
        "Related PO-32 protocol is a hypothesis, not established PO-33 compatibility.",
        "Constant plaintext is not assumed to exist merely because sounds/patterns were cleared.",
        "Same value mapping on both channels; independent mappings and reversed stereo order untested.",
        "Search excludes repeated acquisition prefix and terminal carrier; no arrays are rewritten.",
        "Matching or failure does not establish payload framing, checksum or editable fields.",
    ]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--extra-phase-views", action="store_true")
    p.add_argument("--minimum-run-bytes", type=int, default=16)
    args = p.parse_args()
    validate_outputs([args.out], [args.artifact], False)
    write_bytes(
        args.out,
        json_bytes(run(args.artifact, args.extra_phase_views, args.minimum_run_bytes)),
    )


if __name__ == "__main__":
    main()
