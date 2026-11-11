"""Test bounded CRC frame guesses suggested by the post-observation 520 increment period."""

import argparse
from itertools import permutations
from pathlib import Path

import numpy as np

from po33_re.analysis.checksums import scan_frame_offsets, validate_frame_candidate
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def pack_window(x, begin, mapping):
    count = (len(x) - begin) // 4 * 4
    weights = np.array([1, 4, 16, 64], dtype=np.uint16)
    mapped = np.array(mapping, dtype=np.uint8)[x[begin : begin + count]]
    return np.sum(mapped.reshape(-1, 4).astype(np.uint16) * weights, axis=1).astype(np.uint8)


def run(path):
    artifact = load_artifact(path)
    report = {
        "analysis_version": "bounded-frame-crcs-0.1",
        "artifact": str(path),
        "artifact_sha256": sha256_file(path),
        "source_sha256": artifact.metadata["source_sha256"],
        "training_region_start_values": 1179200,
        "selection": "Post-observation; candidate 520-value structure, not verified framing",
        "crc16_comparisons": 0,
        "crc32_comparisons": 0,
        "hits": [],
        "payload_decoded": False,
    }
    mappings = list(permutations(range(4)))
    for view in (
        "raw_labels",
        "staggered_phase",
        "staggered_increments",
        "staggered_coordinate_xor",
    ):
        values = [artifact.left_symbols, artifact.right_symbols]
        if view != "raw_labels":
            values = [staggered_phases(x) for x in values]
        if view == "staggered_increments":
            values = [phase_increments(x) for x in values]
        if view == "staggered_coordinate_xor":
            values = [x[:-1] ^ x[1:] for x in values]
        if min(map(len, values)) < 1220000:
            raise ValueError("Insufficient labels for fixed checksum training/holdout")
        for offset in range(4):
            begin = 1179200 + offset
            # Bounded holdout needs 75 candidate lengths, not the whole remaining capture.
            blocks = [
                [pack_window(x[begin : begin + 40000], 0, m) for m in mappings] for x in values
            ]
            for channel, choices in zip(("left", "right"), blocks):
                for mi, data in enumerate(choices):
                    checks, hits = scan_frame_offsets(data[:260].tobytes(), 128, 16)
                    report["crc16_comparisons"] += checks
                    for hit in hits:
                        report["hits"].append(
                            {
                                "model": "per_channel_128bytes_crc16_ccitt",
                                "view": view,
                                "channel": channel,
                                "symbol_offset": offset,
                                "label_permutation": list(mappings[mi]),
                                "candidate": hit,
                                **validate_frame_candidate(data.tobytes(), 128, 16, hit),
                            }
                        )
            for li, left in enumerate(blocks[0]):
                for ri, right in enumerate(blocks[1]):
                    training = np.column_stack((left[:260], right[:260])).ravel().tobytes()
                    checks, hits = scan_frame_offsets(training, 256, 32)
                    report["crc32_comparisons"] += checks
                    for hit in hits:
                        data = np.column_stack((left, right)).ravel().tobytes()
                        report["hits"].append(
                            {
                                "model": "interleaved_256bytes_crc32_zip",
                                "view": view,
                                "symbol_offset": offset,
                                "left_permutation": list(mappings[li]),
                                "right_permutation": list(mappings[ri]),
                                "candidate": hit,
                                **validate_frame_candidate(data, 256, 32, hit),
                            }
                        )
    report["limits"] = [
        "CRC16 polynomial 0x1021; initial 0/FFFF, final XOR 0/FFFF, both endiannesses.",
        "CRC32 is Python zlib default ZIP-compatible CRC, both stored endiannesses.",
        "First mapped label occupies low two bits; per-channel bytes interleave left then right.",
        "No symbol-interleaved layout, reversed pair time order, other polynomials or header coverage tested.",
        "Only real consecutive samples used, not artificial wrapping of a nonperiodic raw-phase ring.",
        "Single-block hits require independent holdout; failure does not disprove all validation/coding.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    validate_outputs([args.out], [args.artifact], False)
    write_bytes(args.out, json_bytes(run(args.artifact)))


if __name__ == "__main__":
    main()
