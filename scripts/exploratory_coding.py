"""Reproduce narrowly specified word and bit-anchor probes; no payload interpretation."""

import argparse
from collections import Counter
from itertools import pairwise
from pathlib import Path

import numpy as np

from po33_re.analysis.coding import phase_coordinates
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.symbols import load_artifact, pack_symbols


def run(baseline_path: Path, variant_path: Path) -> dict:
    baseline, variant = load_artifact(baseline_path), load_artifact(variant_path)
    if baseline.metadata["phase_convention"] != variant.metadata["phase_convention"]:
        raise ValueError("Different phase conventions")
    if (
        min(
            len(baseline.left_symbols),
            len(baseline.right_symbols),
            len(variant.left_symbols),
            len(variant.right_symbols),
        )
        < 600000
    ):
        raise ValueError("Fixed exploratory windows require at least 600000 symbols per channel")
    output = {
        "schema_version": 1,
        "analysis_version": "fixed-exploratory-probes-0.1",
        "baseline_artifact_sha256": sha256_file(baseline_path),
        "variant_artifact_sha256": sha256_file(variant_path),
        "source_sha256": baseline.metadata["source_sha256"],
        "variant_source_sha256": variant.metadata["source_sha256"],
        "phase_convention": baseline.metadata["phase_convention"],
        "payload_decoded": False,
        "alignment_applied": False,
        "word_feedback": [],
        "word_alphabets": [],
        "anchor_probes": [],
    }
    first, end = 200000, 240000
    for swap in (False, True):
        x, y = baseline.right_symbols[first:end], variant.right_symbols[first:end]
        if swap:
            x, y = (x >> 1) | ((x & 1) << 1), (y >> 1) | ((y & 1) << 1)
        xb, _ = pack_symbols(x)
        yb, _ = pack_symbols(y)
        for width in (1, 2, 4, 8):
            for endian in ("little", "big"):
                if width == 1 and endian == "big":
                    continue
                mask = (1 << (8 * width)) - 1
                a = [
                    int.from_bytes(xb[i : i + width], endian)
                    for i in range(0, len(xb) - width + 1, width)
                ]
                b = [
                    int.from_bytes(yb[i : i + width], endian)
                    for i in range(0, len(yb) - width + 1, width)
                ]
                delta = [(v - u) & mask for u, v in zip(a, b)]
                modes = Counter(delta)
                ratios = Counter(
                    (v * pow(u, -1, mask + 1)) & mask for u, v in pairwise(delta) if u & 1
                )
                best = ratios.most_common(1)
                output["word_feedback"].append(
                    {
                        "channel": "right",
                        "symbol_window": [first, end],
                        "coordinate_pair_swapped": swap,
                        "word_bytes": width,
                        "endian": endian,
                        "words": len(delta),
                        "modal_modular_difference": modes.most_common(1)[0][0],
                        "modal_difference_fraction": modes.most_common(1)[0][1] / len(delta),
                        "eligible_odd_predecessors": sum(ratios.values()),
                        "most_common_multiplier": best[0][0] if best else None,
                        "multiplier_fraction": best[0][1] / sum(ratios.values()) if best else None,
                    }
                )
    left = phase_coordinates(baseline.left_symbols[200000:600000])
    right = phase_coordinates(baseline.right_symbols[200000:600000])
    for name, bits in (
        ("left", left.ravel()),
        ("right", right.ravel()),
        ("stereo", np.column_stack((left, right)).ravel()),
    ):
        for width in (6, 8, 10, 12, 16, 24):
            choices = []
            for offset in range(width):
                count = min(50000, (len(bits) - offset) // width)
                values = np.packbits(
                    bits[offset : offset + count * width].reshape(count, width),
                    axis=1,
                    bitorder="little",
                )
                words = (
                    np.ascontiguousarray(values).view(np.dtype((np.void, values.shape[1]))).ravel()
                )
                choices.append((len(np.unique(words)), offset, count))
            unique, offset, count = min(choices)
            output["word_alphabets"].append(
                {
                    "mapping": name,
                    "symbol_window": [200000, 600000],
                    "word_bits": width,
                    "offsets_tested": width,
                    "rows_limit": 50000,
                    "minimum_observed_unique_words": unique,
                    "offset_at_minimum": offset,
                    "rows_at_minimum": count,
                    "limit": "Finite observed vocabulary in these mappings, not all codebooks",
                }
            )
    for name in ("left", "right"):
        source = phase_coordinates(getattr(baseline, name + "_symbols")).ravel().tobytes()
        bits = phase_coordinates(getattr(variant, name + "_symbols")).ravel()
        targets = (
            ("unchanged_coordinates", bits.tobytes()),
            ("both_signs_inverted", (bits ^ 1).tobytes()),
        )
        for position in (20000, 100000, 200000):
            anchor = source[position : position + 256]
            for transform, target in targets:
                found = target.find(anchor)
                another = target.find(anchor, found + 1) if found >= 0 else -1
                output["anchor_probes"].append(
                    {
                        "channel": name,
                        "anchor_start_coordinate": position,
                        "anchor_length_coordinates": 256,
                        "target_transform": transform,
                        "first_match": found if found >= 0 else None,
                        "multiple_matches": another >= 0,
                        "applied_shift": None,
                    }
                )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("variant", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    validate_outputs([args.out], [args.baseline, args.variant], args.force)
    write_bytes(args.out, json_bytes(run(args.baseline, args.variant)), args.force)


if __name__ == "__main__":
    main()
