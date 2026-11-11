"""Prepare one hash-pinned second-start experiment without broadening public writers."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from po33_re.formats.samples import decode_signed_mulaw
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_sample_start_control import reference_comparison_checks

SOURCE_SHA = "e0563dce21423d54daf1535e98afeeff72e75cf8415fac1ae37315b52e713417"
SOURCE_BODY_SHA = "bdd3c2d38d525c2a098994939b22816db959a2555b292740b7e816b4ee7b62e6"


def replace_experimental_endpoint(frame, endpoint):
    """Only the observed11716/11827 reference and this19716 candidate/inverse."""
    if type(endpoint) is not int or endpoint not in (11827, 19716):
        raise ValueError("Only this experiment's two endpoints are supported")
    indices = sound_groups(frame).get(2)
    if not indices or len(indices) != 1:
        raise ValueError("Expected one Sound3 reference packet")
    index = indices[0]
    packet = frame.packets[index]
    if packet.payload not in (
        bytes.fromhex("c42d0000332e000000"),
        bytes.fromhex("c42d0000044d000000"),
    ):
        raise ValueError("Expected the exact second-start experiment reference")
    owner = sound_data(frame, 0)
    if len(owner) != 65545 or owner[:4] != bytes(4) or owner[8] != 0:
        raise ValueError("Expected the observed zero-start self-owned65536-code buffer")
    packets = list(frame.packets)
    packets[index] = Packet(packet.tag, packet.payload[:4] + endpoint.to_bytes(4, "little") + b"\0")
    return tuple(packets)


def run(directory):
    root = Path(__file__).resolve().parents[1]
    source_path = (
        root
        / "experiments/event-014-b-sound3-start-quarter/derived/analysis-001/capture.symbols.npz"
    )
    evidence_path = root / "experiments/sound3-start-quarter-results-001.json"
    evidence = json.loads(evidence_path.read_text())
    if (
        sha256_file(source_path) != SOURCE_SHA
        or evidence["artifact_sha256"] != SOURCE_SHA
        or not evidence["control_passed"]
        or not evidence["hypothesis_checks"]["first_field_moves_lower"]
    ):
        raise ValueError("The reviewed, exact second-start source is required")
    source = load_artifact(source_path)
    before_bytes = source.to_bytes()
    original = decode_artifact(source)
    if hashlib.sha256(original.encoded_body).hexdigest() != SOURCE_BODY_SHA:
        raise ValueError("Reviewed second-start body differs")
    edited = rebuild_labels(source, replace_experimental_endpoint(original, 19716))
    edited.metadata["transformations"].append(
        {
            "kind": "second-start-single-candidate-endpoint-edit",
            "sound_slot": 3,
            "start_field": 11716,
            "endpoint_field": 19716,
            "hardware_verified": False,
            "source_artifact_sha256": SOURCE_SHA,
        }
    )
    target = decode_artifact(edited)
    registration = {
        "expected_change": {"sound_slot": 3},
        "control_checks": {
            "packet_count": 511,
            "frame_end_byte": 89396,
            "sound3_reference_packet_index": 375,
            "sound3_reference_before_hex": "c42d0000332e000000",
            "sound3_record_size": 9,
            "sound3_owner_id": 0,
            "only_allowed_payload_offsets": [4, 5, 6, 7],
        },
    }
    checks, packets, changes, values = reference_comparison_checks(original, target, registration)
    checks.update(
        exact_candidate_reference=sound_data(target, 2).hex() == "c42d0000044d000000",
        inverse_reproduces_entire_source_body=encode_packets(
            replace_experimental_endpoint(target, 11827)
        )
        == original.encoded_body,
        source_artifact_preserved=source.to_bytes() == before_bytes,
    )
    codes = np.frombuffer(sound_data(target, 0)[9:], dtype=np.uint8)
    preview = resample_poly(decode_signed_mulaw(codes[11716:19716]), 256, 125)
    preview_buffer = io.BytesIO()
    sf.write(preview_buffer, preview, 48000, format="WAV", subtype="FLOAT")
    if not all(checks.values()):
        raise ValueError("Candidate locality/inverse checks failed before output creation")
    directory.mkdir(exist_ok=False)
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    wav_path = directory / "restore-sound3-quarter-window.wav"
    write_bytes(wav_path, waveform)
    write_bytes(directory / "window-preview-48k.wav", preview_buffer.getvalue())
    recovered = decode_wav(wav_path, 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    comparison = compare_artifacts(edited, recovered)
    decoded_frame = decode_artifact(recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        entire_native_body_after_wav_decode=decoded_frame.encoded_body == target.encoded_body,
        entire_plain_packets_after_wav_decode=decoded_frame.packets == target.packets,
        preview_frame_count=len(preview) == 16384,
        source_file_preserved=sha256_file(source_path) == SOURCE_SHA,
    )
    report = {
        "analysis_version": "second-start-single-candidate-0.1",
        "control_evidence_sha256": sha256_file(evidence_path),
        "source_capture_sha256": source.metadata["source_sha256"],
        "source_artifact_sha256": SOURCE_SHA,
        "restore_wav_sha256": sha256_file(wav_path),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound3_header_hex": sound_data(target, 2).hex(),
        "sound3_header_values": values,
        "changed_plain_packet_indices": packets,
        "sound3_reference_byte_changes": changes,
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "packets_after_wav_decode": frame_report(decoded_frame),
        "preview": {
            "start_field": 11716,
            "endpoint_field": 19716,
            "raw_code_count": 8000,
            "sample_rate_hz_nominal": 23437.5,
            "export_sample_rate_hz": 48000,
            "export_frames": len(preview),
            "selection_policy": "Explicit half-open[start,end); device inclusivity unresolved",
        },
        "hardware_verified": False,
        "public_writer_scope_changed": False,
        "limits": [
            "This isolated candidate only changes11827 to19716 at the physically observed start11716",
            "Public endpoint writers and project previews remain limited to the previously accepted start31393",
            "The second-start endpoint interpretation needs this separate hardware restore and audition test",
            "The repeated111 width does not establish general minimum-width quantization or inclusivity",
        ],
    }
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Candidate waveform checks failed; outputs retained for diagnosis")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
