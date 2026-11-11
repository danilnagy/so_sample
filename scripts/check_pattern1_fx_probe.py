"""Retain footer-only, broader Pattern1 and no-change FX alternatives without code fitting."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_volume_probe import raw_changes
from scripts.prepare_pattern1_fx_probe import CAPTURE_ID, REGISTRATION


def fx_report(base, actual, registration):
    if registration["footer_candidate"] != {"pattern": 1, "start_byte": 1024, "bytes": 8}:
        raise ValueError("FX footer candidate differs from preregistered location")
    before, after = [pattern_data(frame, 1) for frame in (base, actual)]
    preservation = {
        "all_nonpattern_packets_and_samples_unchanged": tuple(
            p for p in base.packets if p.tag != 0xC498
        )
        == tuple(p for p in actual.packets if p.tag != 0xC498),
        "other15_patterns_unchanged": all(
            pattern_data(base, index) == pattern_data(actual, index) for index in range(2, 17)
        ),
        "packet_tags_and_lengths_unchanged": [(p.tag, len(p.payload)) for p in base.packets]
        == [(p.tag, len(p.payload)) for p in actual.packets],
    }
    scope = all(preservation.values())
    footer_changed = before[1024:] != after[1024:]
    projections = {}
    for name, data in (("before", before[1024:]), ("after", after[1024:])):
        projections[name] = {
            "raw_footer_hex": data.hex(),
            "low_nibble_first_values": [value for byte in data for value in (byte & 15, byte >> 4)],
            "high_nibble_first_values": [
                value for byte in data for value in (byte >> 4, byte & 15)
            ],
        }
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "actual_native_controls_pass": all(
            encode_packets(frame.packets) == frame.encoded_body for frame in (base, actual)
        )
        and len(actual.packets) == registration["expected_packet_count"]
        and actual.end_byte == registration["expected_frame_end_byte"],
        "preservation_checks": preservation,
        "no_serialized_change": base.encoded_body == actual.encoded_body,
        "footer_changed": footer_changed,
        "only_Pattern1_footer_changed_supported": scope
        and footer_changed
        and before[:1024] == after[:1024],
        "Pattern1_primary_and_auxiliary_unchanged": before[:1024] == after[:1024],
        "broader_Pattern1_change_supported": scope and before != after,
        "raw_footer_projections": projections,
        "after_footer_nibbles_uniform": len(set(projections["after"]["low_nibble_first_values"]))
        == 1,
        "raw_payload_changes": raw_changes(base, actual),
        "raw_FX_code_guessed": False,
        "effect_encoding_order_or_UI_mapping_confirmed": False,
        "FX_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    directory = root / "experiments" / CAPTURE_ID
    source_path = root / registration["source_artifact"]
    capture_path = directory / "capture.wav"
    artifact_path = directory / "derived/analysis-001/capture.symbols.npz"
    observation_path = (
        root / "experiments/edited-sound3-filter16-B32-middle-001/hardware-observation-001.json"
    )
    output = directory / "FX-probe-results-001.json"
    validate_outputs([output], [registration_path, source_path, capture_path, artifact_path], False)
    recorded = load_artifact(artifact_path)
    if (
        sha256_file(source_path) != registration["source_artifact_sha256"]
        or sha256_file(root / registration["source_capture"])
        != registration["source_capture_sha256"]
        or sha256_file(observation_path) != registration["source_observation_sha256"]
        or recorded.metadata["source_sha256"] != sha256_file(capture_path)
    ):
        raise ValueError("Registered FX baseline or independent capture identity differs")
    actual = decode_artifact(recorded)
    report = fx_report(decode_artifact(load_artifact(source_path)), actual, registration)
    report.update(
        analysis_version="recorded-Pattern1-FX7-footer-location-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        capture_sha256=sha256_file(capture_path),
        artifact_sha256=sha256_file(artifact_path),
        artifact_path=artifact_path.relative_to(root).as_posix(),
        native_frame=frame_report(actual),
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["source_body_matches_registration"] or not report["actual_native_controls_pass"]:
        raise ValueError("FX native control failed; report retained")


if __name__ == "__main__":
    main()
