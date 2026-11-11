"""Bounded measured-clock demodulation, preserving the original crossing artifact.

Only a pre-frame prefix chooses quarter alignment. All payload signs come from
the waveform; no target packet data, checksum repair or per-payload fitting is used.
The windowed clock leaves unobserved capture edges, so its artifact is for native
packet inspection and must not be directly waveform encoded.
"""

import hashlib

import numpy as np

from ..analysis.waveform import amplitude_clock, sample_quarters
from ..artifacts import sha256_file
from ..audio import load_pcm_wav
from ..formats.packets import decode_artifact, encode_packets, frame_report
from .symbols import PHASE_CONVENTION, SCHEMA, SymbolArtifact, validate_symbols

DECODER_VERSION = "amplitude-clock-0.1"


def recover_channel(values, rate, reference):
    validate_symbols(reference)
    if len(reference) < 2176:
        raise ValueError("At least2176 acquisition labels required for pre-frame alignment")
    centers, correction, clock = amplitude_clock(values, rate)
    quarters, signs, amplitudes = sample_quarters(values, rate, centers, correction)
    candidates = []
    for offset in range(4):
        count = (len(signs) - offset) // 4
        if count < 2048:
            continue
        groups = signs[offset : offset + count * 4].reshape(-1, 4)
        labels = ((groups[:, 0] << 1) | groups[:, 1]).astype(np.uint8)
        for start in range(128):
            if np.array_equal(labels[:2048], reference[start : start + 2048]):
                candidates.append((offset, start))
    if len(candidates) != 1:
        raise ValueError("Measured clock requires one exact pre-frame quarter alignment")
    offset, start = candidates[0]
    count = (len(signs) - offset) // 4
    groups = signs[offset : offset + count * 4].reshape(-1, 4)
    labels = ((groups[:, 0] << 1) | groups[:, 1]).astype(np.uint8)
    expected = np.column_stack(
        (
            labels[:-1] >> 1,
            labels[:-1] & 1,
            1 - (labels[1:] >> 1),
            1 - (labels[:-1] & 1),
        )
    )
    errors = np.count_nonzero(groups[:-1] != expected, axis=0)
    if np.any(errors):
        raise ValueError("Measured quarter signs disagree with the observed quadrature model")
    recovered = np.r_[reference[:start], labels].astype(np.uint8)
    shared = min(len(recovered), len(reference))
    mismatches = np.flatnonzero(recovered[:shared] != reference[:shared])
    details = {
        "clock": clock,
        "alignment": {
            "candidate_count": 512,
            "exact_candidates": len(candidates),
            "sign_offset": offset,
            "inherited_prefix_span": [0, start],
            "training_span": [start, start + 2048],
            "matching_training_labels": 2048,
            "payload_used_for_alignment": False,
        },
        "measured_label_span": [start, len(recovered)],
        "quarter_index_first": int(quarters[0]),
        "all_four_quarter_checked_cells": len(labels) - 1,
        "quarter_mismatches": errors.tolist(),
        "original_crossing_label_mismatches": len(mismatches),
        "first_original_crossing_mismatch": int(mismatches[0]) if len(mismatches) else None,
        "clock_center_frame_span": [float(centers[0]), float(centers[-1])],
        "unobserved_clock_tail_frames": float(len(values) - 1 - centers[-1]),
        "sampled_incomplete_quarter_bits": signs[offset + count * 4 :].tolist(),
        "sampled_absolute_amplitude_quantiles": np.quantile(
            abs(amplitudes), [0, 0.01, 0.5, 0.99]
        ).tolist(),
    }
    return recovered, details


def decode_clock_wav(path, acquisition):
    acquisition.validate()
    digest = sha256_file(path)
    if digest != acquisition.metadata["source_sha256"]:
        raise ValueError("Acquisition artifact does not match the source WAV")
    samples, info = load_pcm_wav(path)
    if info["sample_rate_hz"] != acquisition.metadata["sample_rate_hz"]:
        raise ValueError("Acquisition sample rate differs from WAV")
    streams, channels, details = [], {}, {}
    for index, ch in enumerate(("left", "right")):
        bounds = acquisition.metadata["channels"][ch]["boundaries"]
        start, last = bounds.get("first_significant_sample"), bounds.get("last_significant_sample")
        if type(start) is not int or type(last) is not int or not 0 <= start < last < len(samples):
            raise ValueError("Reviewed acquisition amplitude bounds required")
        labels, detail = recover_channel(
            samples[start : last + 1, index],
            info["sample_rate_hz"],
            getattr(acquisition, ch + "_symbols"),
        )
        streams.append(labels)
        detail["source_amplitude_crop_frames"] = [start, last + 1]
        details[ch] = detail
        channels[ch] = {
            "symbol_count": len(labels),
            "boundaries": {
                "first_significant_sample": start,
                "last_significant_sample": last,
                "inherited_prefix_span": detail["alignment"]["inherited_prefix_span"],
                "measured_label_span": detail["measured_label_span"],
                "complete_capture_boundary_accounting": False,
            },
            "discarded_samples": {
                "unobserved_clock_tail_frames": detail["unobserved_clock_tail_frames"],
                "note": "Fixed windowed clock coverage; original WAV and acquisition artifact preserved, no inferred capture ending",
            },
            "uncertainty": {
                "status": "experimental_windowed_clock_artifact",
                "all_four_quarter_checked_cells": detail["all_four_quarter_checked_cells"],
                "quarter_mismatches": detail["quarter_mismatches"],
            },
            "boundary_sign_intervals": {
                "sampled_incomplete_quarter_bits": detail["sampled_incomplete_quarter_bits"],
                "capture_final_intervals_not_inferred": True,
            },
        }
    acquisition_hash = hashlib.sha256(acquisition.to_bytes()).hexdigest()
    metadata = {
        "schema": SCHEMA,
        "schema_version": 1,
        "phase_convention": PHASE_CONVENTION,
        "source_sha256": digest,
        "channel_order": ["left", "right"],
        **info,
        "decoder_version": DECODER_VERSION,
        "transport_extent": "partial_clock_window",
        "channels": channels,
        "transformations": [
            {
                "kind": "measured-clock-quarter-demodulation",
                "acquisition_artifact_sha256": acquisition_hash,
                "target_data_used": False,
                "original_capture_and_acquisition_preserved": True,
            }
        ],
        "hardware_verified": False,
    }
    artifact = SymbolArtifact(*streams, metadata)
    artifact.validate()
    frame = decode_artifact(artifact)
    if encode_packets(frame.packets) != frame.encoded_body:
        raise ValueError("Recovered native packet body does not re-encode exactly")
    report = {
        "decoder_version": DECODER_VERSION,
        "source_sha256": digest,
        "acquisition_artifact_sha256": acquisition_hash,
        "channels": details,
        "native_frame": frame_report(frame),
        "exact_body_reencode": True,
        "target_data_used": False,
        "hardware_verified": False,
        "limits": [
            "Prefix alignment uses only2048 pre-frame acquisition labels; payload data never selects alignment.",
            "Every interior four-quarter relation and every native packet checksum must pass; no symbol or checksum repair is performed.",
            "Fixed clock windows leave unobserved capture edges. This artifact cannot be directly waveform encoded; rebuild the verified packet frame if needed.",
        ],
    }
    return artifact, report
