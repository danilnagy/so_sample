"""Cross-check captured quarter signs using an amplitude-derived clock."""

import argparse
from pathlib import Path

import numpy as np

from po33_re.analysis.waveform import amplitude_clock, sample_quarters
from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.audio import load_pcm_wav
from po33_re.modem.symbols import load_artifact


def run(audio_path, artifact_path):
    artifact = load_artifact(artifact_path)
    digest = sha256_file(audio_path)
    if digest != artifact.metadata["source_sha256"]:
        raise ValueError("Audio does not match artifact source hash")
    samples, info = load_pcm_wav(audio_path)
    rate = info["sample_rate_hz"]
    report = {
        "analysis_version": "amplitude-clock-probes-0.1",
        "source_sha256": digest,
        "artifact_sha256": sha256_file(artifact_path),
        "source": str(audio_path),
        "channels": {},
        "payload_decoded": False,
    }
    for index, ch in enumerate(("left", "right")):
        bounds = artifact.metadata["channels"][ch]["boundaries"]
        start, end = bounds["first_significant_sample"], bounds["last_significant_sample"] + 1
        values = samples[start:end, index]
        centers, correction, clock = amplitude_clock(values, rate)
        q, signs, amplitudes = sample_quarters(values, rate, centers, correction)
        reference = getattr(artifact, ch + "_symbols")
        candidates = []
        for offset in range(4):
            count = (len(signs) - offset) // 4
            groups = signs[offset : offset + count * 4].reshape(-1, 4)
            labels = (groups[:, 0] << 1) | groups[:, 1]
            for ref_start in range(128):
                score = int(
                    np.count_nonzero(labels[:2048] == reference[ref_start : ref_start + 2048])
                )
                candidates.append((score, offset, ref_start))
        score = max(c[0] for c in candidates)
        winners = [c for c in candidates if c[0] == score]
        _, offset, ref_start = winners[0]
        count = (len(signs) - offset) // 4
        groups = signs[offset : offset + count * 4].reshape(-1, 4)
        labels = (groups[:, 0] << 1) | groups[:, 1]
        shared = min(len(labels), len(reference) - ref_start)
        mismatches = np.flatnonzero(labels[:shared] != reference[ref_start : ref_start + shared])
        # Encoder prediction for all four quarter midpoints in each complete cell.
        n = min(count - 1, len(reference) - ref_start - 1)
        ref = reference[ref_start : ref_start + n + 1]
        expected = np.column_stack(
            (ref[:-1] >> 1, ref[:-1] & 1, 1 - (ref[1:] >> 1), 1 - (ref[:-1] & 1))
        )
        per_quarter = np.count_nonzero(groups[:n] != expected, axis=0)
        report["channels"][ch] = {
            "clock": clock,
            "amplitude_crop_frames": [start, end],
            "quarter_index_first": int(q[0]),
            "alignment_selection": {
                "training_reference_span": [ref_start, ref_start + 2048],
                "candidate_count": len(candidates),
                "tied_best_candidates": len(winners),
                "matching_training_labels": score,
                "sign_offset": offset,
                "reference_start": ref_start,
            },
            "compared_reference_span": [ref_start, ref_start + shared],
            "label_mismatches": len(mismatches),
            "first_mismatched_reference_indices": (mismatches[:32] + ref_start).tolist(),
            "all_four_quarter_check_symbols": n,
            "quarter_mismatches": per_quarter.tolist(),
            "absolute_sampled_amplitude_quantiles": np.quantile(
                abs(amplitudes), [0, 0.01, 0.5, 0.99]
            ).tolist(),
        }
    report["limits"] = [
        "Amplitude bounds reused from artifact; clock uses no measured crossings.",
        "Acquisition quarter offset and whole-cycle position selected only from repeated prefix.",
        "Incomplete edge windows are excluded explicitly from this independent diagnostic.",
        "Coordinate/sign agreement does not establish payload interpretation or framing.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    validate_outputs([args.out], [args.audio, args.artifact], False)
    write_bytes(args.out, json_bytes(run(args.audio, args.artifact)))


if __name__ == "__main__":
    main()
