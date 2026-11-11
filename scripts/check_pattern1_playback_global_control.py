"""Test plain playback separately from FX; preserve failed predictions literally."""

import argparse
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import Packet, decode_artifact, encode_packets, frame_report
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_volume_probe import raw_changes
from scripts.prepare_pattern1_playback_global_control import CAPTURE_IDS, REGISTRATION


def global_only_preserved(base, actual, mask):
    if mask not in (15, 255):
        raise ValueError("Fixed low-four/whole-byte alternatives required")
    normalized = []
    for frame in (base, actual):
        if frame.packets[2].tag != 0x7D5C or len(frame.packets[2].payload) != 255:
            return False
        packets = list(frame.packets)
        payload = bytearray(packets[2].payload)
        payload[131] &= 255 ^ mask
        packets[2] = Packet(packets[2].tag, bytes(payload))
        normalized.append(tuple(packets))
    return normalized[0] == normalized[1]


def require_independent_captures(source_hash, capture_hashes):
    if len(capture_hashes) != 2 or len({source_hash, *capture_hashes}) != 3:
        raise ValueError(
            "Independent NEW raw WAVs required; duplicate input cannot adjudicate control"
        )


def playback_report(base, repeated, played, registration):
    if registration["global_candidate"] != {
        "packet_index": 2,
        "tag": 32092,
        "payload_offset": 131,
        "narrow_mask": 15,
        "broader_mask": 255,
    }:
        raise ValueError("Global candidate differs from fixed registered alternatives")
    frames = [repeated, played]
    return {
        "source_body_matches_registration": hashlib.sha256(base.encoded_body).hexdigest()
        == registration["source_body_sha256"],
        "all_native_controls_pass": all(
            len(frame.packets) == registration["expected_packet_count"]
            and frame.end_byte == registration["expected_frame_end_byte"]
            and encode_packets(frame.packets) == frame.encoded_body
            for frame in (base, *frames)
        ),
        "stopped_repeat_entire_body_equal_source_prediction": repeated.packets == base.packets
        and repeated.encoded_body == base.encoded_body,
        "both_footers_remain_no_FX": [
            pattern_data(frame, 1)[1024:].hex() == registration["expected_footer_hex"]
            for frame in frames
        ],
        "global_low4_scope_by_leg_against_source": [
            global_only_preserved(base, frame, 15) for frame in frames
        ],
        "global_whole_byte_scope_by_leg_against_source": [
            global_only_preserved(base, frame, 255) for frame in frames
        ],
        "plain_playback_low4_scope_against_repeat": global_only_preserved(repeated, played, 15),
        "plain_playback_whole_byte_scope_against_repeat": global_only_preserved(
            repeated, played, 255
        ),
        "global_values_source_repeat_played": [
            frame.packets[2].payload[131] for frame in (base, *frames)
        ],
        "plain_playback_global_changed_from_repeat_diagnostic": repeated.packets[2].payload[131]
        != played.packets[2].payload[131],
        "raw_changes_against_source": [raw_changes(base, frame) for frame in frames],
        "global_role_or_nibble_order_confirmed": False,
        "FX_writer_enabled": False,
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    source_path = root / registration["source_artifact"]
    folders = [root / "experiments" / name for name in CAPTURE_IDS]
    captures = [folder / "capture.wav" for folder in folders]
    paths = [folder / "derived/analysis-001/capture.symbols.npz" for folder in folders]
    output = root / "experiments/pattern1-playback-global-results-001.json"
    validate_outputs([output], [registration_path, source_path, *captures, *paths], False)
    capture_hashes = [sha256_file(path) for path in captures]
    require_independent_captures(registration["source_capture_sha256"], capture_hashes)
    pins = [
        (source_path, registration["source_artifact_sha256"]),
        (root / registration["source_capture"], registration["source_capture_sha256"]),
        (root / registration["source_observation"], registration["source_observation_sha256"]),
    ]
    recorded = [load_artifact(path) for path in paths]
    if any(sha256_file(path) != digest for path, digest in pins) or any(
        item.metadata["source_sha256"] != digest for item, digest in zip(recorded, capture_hashes)
    ):
        raise ValueError("Frozen source or independent capture identity differs")
    frames = [decode_artifact(item) for item in recorded]
    report = playback_report(decode_artifact(load_artifact(source_path)), *frames, registration)
    report.update(
        analysis_version="opaque-global131-repeat-and-plain-playback-check-0.1",
        hardware_verified=False,
        registration_sha256=sha256_file(registration_path),
        captures=[
            {
                "experiment_id": folder.name,
                "capture_sha256": digest,
                "artifact_sha256": sha256_file(path),
                "artifact_path": path.relative_to(root).as_posix(),
                "native_frame": frame_report(frame),
            }
            for folder, digest, path, frame in zip(folders, capture_hashes, paths, frames)
        ],
        limits=registration["limits"],
    )
    write_bytes(output, json_bytes(report))
    if not report["source_body_matches_registration"] or not report["all_native_controls_pass"]:
        raise ValueError("Playback native control failed; report retained")


if __name__ == "__main__":
    main()
