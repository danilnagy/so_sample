"""Close the independent-channel mapping gap in a finite whitening hypothesis."""

import argparse
from itertools import permutations
from pathlib import Path

from po33_re.analysis.staggered import CIRCULAR_INDEX, phase_increments, staggered_phases
from po33_re.analysis.whitening import (
    REVERSED_BYTE_BITS,
    constant_codebook,
    constant_plaintext_runs,
    stereo_candidate_bytes,
)
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact

VIEWS = {
    "raw": lambda x: x,
    "staggered_phase": staggered_phases,
    "increment": lambda x: phase_increments(staggered_phases(x)),
    "raw_circular_increment": lambda x: phase_increments(CIRCULAR_INDEX[x]),
    "raw_coordinate_xor": lambda x: x[1:] ^ x[:-1],
}


def run(path, view):
    artifact = load_artifact(path)
    pair = [VIEWS[view](getattr(artifact, ch + "_symbols")) for ch in ("left", "right")]
    if min(map(len, pair)) < 43000:
        raise ValueError("Fixed probe requires43000 values per view/channel")
    pair = [x[8500:43000] for x in pair]
    report = {
        "analysis_version": "independent-channel-whitening-0.1",
        "artifact_sha256": sha256_file(path),
        "source_sha256": artifact.metadata["source_sha256"],
        "view": view,
        "window_in_phase_view": [8500, 43000],
        "lead_commit": "3b3a0a758ba452fc809027c5bafcc5e2d0931532",
        "model": "coded=(raw+low8(state)) mod256; state=CRC-CCITT-1021(state,raw)",
        "independent_channel_mappings": True,
        "minimum_run_bytes": 8,
        "candidate_streams": 0,
        "three_byte_candidates": 0,
        "validated_runs": 0,
        "matches": [],
        "payload_decoded": False,
    }
    books = {raw: constant_codebook(raw) for raw in (0, 255)}
    for left_mapping in permutations(range(4)):
        for right_mapping in permutations(range(4)):
            for offset in range(4):
                for layout in ("stereo_symbols", "stereo_bytes"):
                    for right_first in (False, True):
                        data = stereo_candidate_bytes(
                            *pair, left_mapping, right_mapping, offset, layout, right_first
                        )
                        for reverse_bits in (False, True):
                            coded = REVERSED_BYTE_BITS[data] if reverse_bits else data
                            report["candidate_streams"] += 1
                            for raw, book in books.items():
                                result = constant_plaintext_runs(coded, raw, book=book, minimum=8)
                                report["three_byte_candidates"] += result["three_byte_candidates"]
                                report["validated_runs"] += result["validated_runs"]
                                if result["validated_runs"]:
                                    report["matches"].append(
                                        {
                                            "left_mapping": list(left_mapping),
                                            "right_mapping": list(right_mapping),
                                            "offset": offset,
                                            "layout": layout,
                                            "right_first": right_first,
                                            "reversed_byte_bits": reverse_bits,
                                            **result,
                                        }
                                    )
    report["limits"] = [
        "Constant plaintext0/255 and this16-bit update are finite related-device hypotheses.",
        "All65536 seed states are considered; first3 bytes select candidates and>=5 additional bytes must match.",
        "Same temporal channel offset; separate channel delays and other CRC/whitening rules untested.",
        "Enumerated streams may overlap or be equivalent; counts are not independent statistical trials.",
        "No artifact rewrite, native framing, checksum or editable field is inferred.",
    ]
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", type=Path)
    p.add_argument("--view", choices=VIEWS, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    validate_outputs([args.out], [args.artifact], False)
    write_bytes(args.out, json_bytes(run(args.artifact, args.view)))


if __name__ == "__main__":
    main()
