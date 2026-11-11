"""Keep original strict failure separate from new footer/global hypotheses and clear return."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, frame_report
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_pattern1_fx_probe import fx_report
from scripts.prepare_pattern1_fx_return_controls import CAPTURE_IDS, REGISTRATION


def footer_global_preserved(base, actual, mask):
    if mask not in (15, 255):
        raise ValueError("Fixed low-four/whole global-byte masks required")
    if any(
        frame.packets[2].tag != 0x7D5C or len(frame.packets[2].payload) != 255
        for frame in (base, actual)
    ):
        return False
    normalized = []
    for frame in (base, actual):
        data = bytearray(pattern_data(frame, 1))
        data[1024:] = bytes(8)
        packets = list(_replace_pattern_data(frame, 1, bytes(data)))
        payload = bytearray(packets[2].payload)
        payload[131] &= 255 ^ mask
        packets[2] = Packet(packets[2].tag, bytes(payload))
        normalized.append(tuple(packets))
    return normalized[0] == normalized[1]


def return_report(base, octave_down, cleared, independent_no_FX, registration):
    if registration["global_candidate"] != {
        "packet_index": 2,
        "tag": 32092,
        "payload_offset": 131,
        "narrow_mask": 15,
        "broader_mask": 255,
    }:
        raise ValueError("Global candidate differs from fixed preregistered alternatives")
    frames = [octave_down, cleared]
    reports = [fx_report(base, frame, registration) for frame in frames]
    return {
        "source_body_matches_registration": all(
            report["source_body_matches_registration"] for report in reports
        ),
        "both_actual_native_controls_pass": all(
            report["actual_native_controls_pass"] for report in reports
        ),
        "independent_no_FX_body_matches_registration": hashlib.sha256(
            independent_no_FX.encoded_body
        ).hexdigest()
        == registration["independent_no_FX_body_sha256"],
        "footer_plus_global_low4_scope_by_leg": [
            footer_global_preserved(base, frame, 15) for frame in frames
        ],
        "footer_plus_global_whole_byte_scope_by_leg": [
            footer_global_preserved(base, frame, 255) for frame in frames
        ],
        "footer_mapping_prediction_matches_by_leg": [
            pattern_data(frame, 1)[1024:].hex() == leg["expected_footer_hex"]
            for frame, leg in zip(frames, registration["expected_capture_sequence"])
        ],
        "global_byte_values_by_leg": [frame.packets[2].payload[131] for frame in frames],
        "clear_matches_independent_no_FX_except_global131": cleared.packets
        == independent_no_FX.packets
        or (
            pattern_data(cleared, 1)[1024:] == pattern_data(independent_no_FX, 1)[1024:]
            and footer_global_preserved(independent_no_FX, cleared, 255)
        ),
        "clear_entire_body_and_packets_equal_independent_no_FX_diagnostic": cleared.encoded_body
        == independent_no_FX.encoded_body
        and cleared.packets == independent_no_FX.packets,
        "literal_location_reports_against_FX7": reports,
        "global_byte_meaning_or_nibble_order_confirmed": False,
        "FX_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    baseline_path = root / registration["independent_no_FX_artifact"]
    directories = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [directory / "capture.wav" for directory in directories]
    paths = [directory / "derived/analysis-001/capture.symbols.npz" for directory in directories]
    output = root / "experiments/pattern1-FX8-clear-results-001.json"
    validate_outputs(
        [output], [registration_path, source_path, baseline_path, *captures, *paths], False
    )
    recorded = [load_artifact(path) for path in paths]
    observation_path = (
        root / "experiments/event-065-a-pattern1-FX7-recorded/hardware-observation-001.json"
    )
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(observation_path) != registration["source_observation_sha256"]
        or sha256_file(baseline_path) != registration["independent_no_FX_artifact_sha256"]
        or any(
            item.metadata["source_sha256"] != sha256_file(capture)
            for item, capture in zip(recorded, captures)
        )
    ):
        raise ValueError("Frozen FX7/baseline or independent capture identity differs")
    frames = [decode_artifact(item) for item in recorded]
    report = return_report(
        decode_artifact(load_artifact(source_path)),
        *frames,
        decode_artifact(load_artifact(baseline_path)),
        registration,
    )
    report.update(
        analysis_version="recorded-FX8-clear-footer-global-candidate-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        captures=[
            {
                "experiment_id": directory.name,
                "capture_sha256": sha256_file(capture),
                "artifact_sha256": sha256_file(path),
                "artifact_path": path.relative_to(root).as_posix(),
                "native_frame": frame_report(frame),
            }
            for directory, capture, path, frame in zip(directories, captures, paths, frames)
        ],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if (
        not report["source_body_matches_registration"]
        or not report["both_actual_native_controls_pass"]
        or not report["independent_no_FX_body_matches_registration"]
    ):
        raise ValueError("FX return native control failed; report retained")


if __name__ == "__main__":
    main()
