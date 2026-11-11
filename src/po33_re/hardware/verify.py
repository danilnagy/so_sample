"""Decode a fresh backup immediately and compare it with an expected native target.

Decoding uses the established crossing threshold first. If that does not yield a
checksum-valid frame, two fallbacks are tried in order:

1. Leading-label realignment: drop 1..3 leading labels from one channel, only while they
   repeat the channel's first label (the steady carrier before the frame). On 2026-10-10
   two backups of one state each had one extra carrier label on the left channel and
   failed at the frame start; dropping it recovered all 815 packets.
2. The measured-clock decoder from the crossing acquisition, as was done by hand for
   earlier timing-slip recordings.

Whichever method yields a checksum-valid frame is saved as ``capture.symbols.npz``
with ``decode.json``, so existing check scripts read it unchanged. Other attempts keep
their own file names. Every attempt and its outcome are reported; nothing is fitted
to the target.
"""

import copy
import hashlib

from ..artifacts import json_bytes, sha256_file, write_bytes
from ..audio import inspect_wav
from ..formats.packets import decode_artifact, encode_packets, frame_report
from ..modem.clock_decode import decode_clock_wav
from ..modem.decode import DecodeFailure, decode_wav
from ..modem.symbols import SymbolArtifact
from .changes import describe_changes

ESTABLISHED_THRESHOLD = 0.0063


class CaptureAnalysis:
    def __init__(self, report, frame):
        self.report = report
        self.frame = frame

    @property
    def decoded(self):
        return self.frame is not None


def _frame_or_error(artifact):
    try:
        frame = decode_artifact(artifact)
    except ValueError as exc:
        return None, str(exc)
    if encode_packets(frame.packets) != frame.encoded_body:
        return None, "Recovered packets do not re-encode to the captured body"
    return frame, None


MAX_LEADING_LABELS = 3


def realigned_artifacts(artifact):
    """Yield (description, artifact) dropping repeated leading carrier labels per channel."""
    for channel in ("left", "right"):
        labels = getattr(artifact, f"{channel}_symbols")
        for drop in range(1, MAX_LEADING_LABELS + 1):
            if len(labels) <= drop or any(labels[i] != labels[0] for i in range(drop + 1)):
                break
            metadata = copy.deepcopy(artifact.metadata)
            metadata["channels"][channel]["symbol_count"] = len(labels) - drop
            metadata["transformations"] = [
                *metadata["transformations"],
                {
                    "kind": "leading-carrier-label-realignment",
                    "channel": channel,
                    "dropped_leading_labels": drop,
                    "dropped_label_value": int(labels[0]),
                    "target_data_used": False,
                },
            ]
            left = artifact.left_symbols[drop:] if channel == "left" else artifact.left_symbols
            right = artifact.right_symbols[drop:] if channel == "right" else artifact.right_symbols
            candidate = SymbolArtifact(left, right, metadata)
            candidate.validate()
            yield {"channel": channel, "dropped_leading_labels": drop}, candidate


def analyze_capture(capture, analysis_dir, threshold=ESTABLISHED_THRESHOLD, clock_fallback=True):
    """Decode ``capture`` into a fresh ``analysis_dir`` using the standard file names."""
    if analysis_dir.exists():
        raise ValueError(f"Analysis directory already exists: {analysis_dir}")
    analysis_dir.mkdir(parents=True)
    levels = inspect_wav(capture)
    capture_hash = sha256_file(capture)
    report = {
        "capture_sha256": capture_hash,
        "levels": {
            "sample_rate_hz": levels["sample_rate_hz"],
            "pcm_subtype": levels["pcm_subtype"],
            "duration_seconds": levels["duration_seconds"],
            "peaks_per_channel": [
                levels["channels"][c]["peak_amplitude"] for c in ("left", "right")
            ],
            "possible_clipping": any(
                levels["channels"][c]["possible_clipping"] for c in ("left", "right")
            ),
        },
        "attempts": [],
        "method": None,
        "native": None,
        "hardware_verified": False,
    }
    artifacts = {}

    def finish(method, frame):
        chosen = artifacts.get(method) or artifacts.get("crossing")
        if chosen is not None:
            encoded = chosen.to_bytes()
            write_bytes(analysis_dir / "capture.symbols.npz", encoded)
            decode_report = {
                **chosen.metadata,
                "artifact_sha256": hashlib.sha256(encoded).hexdigest(),
            }
            write_bytes(analysis_dir / "decode.json", json_bytes(decode_report))
        for name, artifact in artifacts.items():
            if artifact is not chosen:
                write_bytes(analysis_dir / f"{name}.symbols.npz", artifact.to_bytes())
        report["method"] = method if frame is not None else None
        if frame is not None:
            report["native"] = frame_report(frame)
        write_bytes(analysis_dir / "harness-analysis.json", json_bytes(report))
        return CaptureAnalysis(report, frame)

    try:
        crossing = decode_wav(capture, threshold)
    except DecodeFailure as exc:
        report["attempts"].append(
            {"method": "crossing", "threshold": threshold, "passed": False, "error": str(exc)}
        )
        crossing = None
    if crossing is not None:
        artifacts["crossing"] = crossing
        frame, error = _frame_or_error(crossing)
        report["attempts"].append(
            {
                "method": "crossing",
                "threshold": threshold,
                "passed": frame is not None,
                "error": error,
            }
        )
        if frame is not None:
            return finish("crossing", frame)

    if crossing is not None:
        for description, candidate in realigned_artifacts(crossing):
            frame, error = _frame_or_error(candidate)
            if frame is not None:
                artifacts["realigned"] = candidate
                report["attempts"].append(
                    {"method": "realigned", **description, "passed": True, "error": None}
                )
                return finish("realigned", frame)
        report["attempts"].append(
            {
                "method": "realigned",
                "passed": False,
                "error": "No leading-label realignment decoded",
            }
        )

    if clock_fallback and crossing is not None:
        try:
            clock_artifact, clock_report = decode_clock_wav(capture, crossing)
            artifacts["measured_clock"] = clock_artifact
            write_bytes(analysis_dir / "clock-decode.json", json_bytes(clock_report))
            frame, error = _frame_or_error(clock_artifact)
        except (ValueError, DecodeFailure) as exc:
            frame, error = None, str(exc)
        report["attempts"].append(
            {"method": "measured_clock", "passed": frame is not None, "error": error}
        )
        if frame is not None:
            return finish("measured_clock", frame)
    return finish(None, None)


def compare_with_target(target_frame, frame):
    """Exact native comparison plus a device-level description of any difference."""
    description = describe_changes(target_frame, frame)
    return {
        "exact_target_body": description["identical_body"],
        "target_body_sha256": hashlib.sha256(target_frame.encoded_body).hexdigest(),
        "captured_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "differences_from_target": description,
    }
