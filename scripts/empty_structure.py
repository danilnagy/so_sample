"""Reproduce bounded single-state probes and capture-threshold diagnostics."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.coding import (
    berlekamp_massey,
    phase_coordinates,
    recurrence_errors,
    recurrence_probe,
    repeated_prefix,
)
from po33_re.analysis.periodicity import lag_runs, lag_similarity
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.modem.decode import DecodeFailure, decode_wav
from po33_re.modem.symbols import load_artifact


def run(artifact_path, audio_paths):
    artifact = load_artifact(artifact_path)
    report = {
        "analysis_version": "empty-state-structure-0.2",
        "artifact_sha256": sha256_file(artifact_path),
        "source_sha256": artifact.metadata["source_sha256"],
        "window_start": 8500,
        "phase_views": {},
        "prefix": {},
        "threshold_probes": [],
        "payload_decoded": False,
    }
    for channel in ("left", "right"):
        raw = getattr(artifact, channel + "_symbols")
        if len(raw) < 43000:
            raise ValueError("Fixed empty-state recurrence windows require43000 labels")
        report["prefix"][channel] = repeated_prefix(raw)
        for view in (
            "raw_labels",
            "staggered_phase",
            "staggered_increments",
            "staggered_coordinate_xor",
        ):
            x = raw if view == "raw_labels" else staggered_phases(raw)
            if view == "staggered_increments":
                x = phase_increments(x)
            if view == "staggered_coordinate_xor":
                x = x[1:] ^ x[:-1]
            lanes = phase_coordinates(x)
            probes = [recurrence_probe(lanes[8500:9524, i]) for i in (0, 1)]
            checked = 0
            candidates = []
            for stride in range(1, 33):
                for offset in range(stride):
                    for lane in (0, 1):
                        bits = lanes[8500 + offset : 8500 + offset + stride * 1024 : stride, lane]
                        fit = berlekamp_massey(bits[:512], max_degree=32)
                        checked += 1
                        if fit["complete"]:
                            candidates.append(
                                {
                                    "stride": stride,
                                    "offset": offset,
                                    "lane": lane,
                                    "degree": fit["degree"],
                                    "holdout_errors": recurrence_errors(bits, fit["tap_lags"], 512),
                                }
                            )
            similarity = lag_similarity(x[8500:], 2048)
            indices = np.argsort(similarity)[-8:][::-1]
            report["phase_views"][channel + "_" + view] = {
                "probes": probes,
                "decimated_mappings": checked,
                "small_candidates": candidates,
                "lag_similarity_span": [8500, len(x)],
                "best_lags": [
                    {"lag": int(i + 1), "equal_fraction": float(similarity[i])} for i in indices
                ],
                "longest_lag520_runs": lag_runs(x, 520, limit=3),
            }
    for path in audio_paths:
        entry = {"capture": str(path), "source_sha256": sha256_file(path), "profiles": []}
        for threshold in (0.0025, 0.004, 0.0063):
            profile = {"threshold": threshold}
            try:
                decoded = decode_wav(path, threshold)
                profile["decoder_version"] = decoded.metadata["decoder_version"]
                profile.update(status="decoded", channels={})
                for channel in ("left", "right"):
                    values = getattr(decoded, channel + "_symbols")
                    profile["channels"][channel] = {
                        "symbols": len(values),
                        "matches_reference_labels_and_counts": bool(
                            np.array_equal(values, getattr(artifact, channel + "_symbols"))
                        ),
                        "incomplete_final_sign_intervals": decoded.metadata["channels"][channel][
                            "boundary_sign_intervals"
                        ]["incomplete_final_cycle_bits"],
                    }
            except DecodeFailure as exc:
                profile.update(status="decode_failed", reason=str(exc))
            entry["profiles"].append(profile)
        report["threshold_probes"].append(entry)
    report["limits"] = [
        "UI-cleared slots do not establish all-zero plaintext or fully erased flash.",
        "Finite single-stream recurrences cannot exclude every coding model.",
        "Threshold changes can alter noise acquisition and partial endpoints even when complete labels match.",
        "No alternate profile is selected to force matching captures; canonical0.0063 remains explicit.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--audio-captures", nargs="*", type=Path, default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    validate_outputs([args.out], [args.artifact, *args.audio_captures], False)
    write_bytes(args.out, json_bytes(run(args.artifact, args.audio_captures)))


if __name__ == "__main__":
    main()
