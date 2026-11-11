"""Search fixed phase-increment anchors without shifting any stored artifact."""

import argparse
from pathlib import Path

from po33_re.analysis.anchors import extend_anchor, find_anchor, packed_offsets
from po33_re.analysis.coding import phase_coordinates
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact


def run(paths):
    artifacts = [load_artifact(p) for p in paths]
    if len({a.metadata["phase_convention"] for a in artifacts}) != 1:
        raise ValueError("Different phase conventions")
    report = {
        "analysis_version": "increment-anchors-0.1",
        "inputs": [
            {
                "path": str(p),
                "artifact_sha256": sha256_file(p),
                "source_sha256": a.metadata["source_sha256"],
            }
            for p, a in zip(paths, artifacts)
        ],
        "anchor_length_coordinates": 256,
        "anchor_increment_positions": sorted(
            {10000, 500000, 1000000, *range(20000, 940000, 32768)}
        ),
        "units": "binary coordinates of circular phase increments; not verified protocol bits",
        "selection": "Post-observation probes; 10000 and 500000 include initially observed hits",
        "alignment_applied": False,
        "payload_decoded": False,
        "probes": [],
    }
    for channel in ("left", "right"):
        arrays = [
            phase_coordinates(
                phase_increments(staggered_phases(getattr(a, channel + "_symbols")))
            ).ravel()
            for a in artifacts
        ]
        streams = [packed_offsets(bits) for bits in arrays]
        for index in range(1, len(arrays)):
            for position in report["anchor_increment_positions"]:
                start = position * 2
                source = arrays[0]
                target = arrays[index]
                if start + 256 > len(source):
                    raise ValueError("Insufficient coordinates for fixed anchors")
                needle = source[start : start + 256]
                self_hits = find_anchor(needle, streams[0], len(source))
                hits = find_anchor(needle, streams[index], len(target))
                report["probes"].append(
                    {
                        "input_indices": [0, index],
                        "channel": channel,
                        "source_start_coordinate": start,
                        "source_hits": self_hits,
                        "target_hits": hits,
                        "source_unique": self_hits["positions"] == [start]
                        and not self_hits["more_than_limit"],
                        "extensions": [
                            extend_anchor(source, target, start, t, 256) for t in hits["positions"]
                        ],
                    }
                )
    report["limits"] = [
        "A repeated source anchor cannot establish unique relocation.",
        "Finite exact matches do not imply whole-stream relocation or identify state fields.",
        "No inversion, permutation or fitted normalization is used in this representation.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    validate_outputs([args.out], args.inputs, False)
    write_bytes(args.out, json_bytes(run(args.inputs)))


if __name__ == "__main__":
    main()
