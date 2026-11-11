"""Prepare a generated Sound6-to7 reference copy before shared-owner deletion tests."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.lifecycle import copy_calibrated_melodic_reference
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from po33_re.formats.patterns import pattern_data
from po33_re.formats.samples import sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data


def copy_owned_reference_to_empty_slot(frame, source_sound, destination_sound):
    """Only observed Sound4-to5 reconstruction and this unshared Sound6-to7 probe."""
    if (source_sound, destination_sound) == (6, 7):
        return copy_calibrated_melodic_reference(frame, source_sound, destination_sound)
    headers = {
        (4, 5): "00000000c06f000003",
        (6, 7): "00000000c078000005",
    }
    if (
        type(source_sound) is not int
        or type(destination_sound) is not int
        or (source_sound, destination_sound) not in headers
    ):
        raise ValueError("Only Sound4-to5 reconstruction and Sound6-to7 are supported")
    owner, destination = source_sound - 1, destination_sound - 1
    groups = sound_groups(frame)
    if destination not in groups or groups[destination]:
        raise ValueError("Destination must be an existing empty selector")
    data = sound_data(frame, owner)
    if len(data) != 32777 or data[:9].hex() != headers[(source_sound, destination_sound)]:
        raise ValueError("Expected the exact zero-start self-owned32768-code source layout")
    referrers = []
    for key, indices in groups.items():
        if not indices:
            continue
        record = sound_data(frame, key)
        if len(record) < 9 or record[8] == destination:
            raise ValueError("Malformed sample or reference to empty destination")
        if record[8] == owner:
            referrers.append(key)
    if referrers != [owner]:
        raise ValueError("Source must currently be unshared")
    index = next(
        i
        for i, packet in enumerate(frame.packets)
        if packet == Packet(0x68B5, bytes([destination]))
    )
    return frame.packets[: index + 1] + (Packet(0xEF78, data[:9]),) + frame.packets[index + 1 :]


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with an existing parent required")
    baseline = root / "experiments/edited-sound6-create-001"
    acceptance_path = baseline / "hardware-acceptance-001.json"
    acceptance = json.loads(acceptance_path.read_text())
    source_path = baseline / "derived/analysis-001/capture.symbols.npz"
    if (
        not acceptance["hardware_verified"]
        or sha256_file(source_path) != acceptance["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != acceptance["capture_sha256"]
    ):
        raise ValueError("Verified Sound6 creation and unchanged source files required")
    source = load_artifact(source_path)
    original = decode_artifact(source)
    original_bytes = source.to_bytes()
    if hashlib.sha256(original.encoded_body).hexdigest() != acceptance["body_sha256"]:
        raise ValueError("Verified source body differs")
    old_base = decode_artifact(
        load_artifact(
            root
            / "experiments/event-022-b-record-independent-sound4/derived/analysis-001/capture.symbols.npz"
        )
    )
    old_copy = decode_artifact(
        load_artifact(
            root
            / "experiments/event-023-b-copy-sound4-to-sound5/derived/analysis-003/capture.symbols.npz"
        )
    )
    reconstructed = encode_packets(copy_owned_reference_to_empty_slot(old_base, 4, 5))
    if reconstructed != old_copy.encoded_body:
        raise ValueError("Independent physical reference-copy reconstruction differs")
    edited = rebuild_labels(source, copy_owned_reference_to_empty_slot(original, 6, 7))
    edited.metadata["transformations"].append(
        {
            "kind": "generated-owned-sound6-to-empty-sound7-reference-copy",
            "source_sound": 6,
            "destination_sound": 7,
            "source_artifact_sha256": acceptance["artifact_sha256"],
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    preview, preview_report = sound_at_48k(target, 7)
    original_preview, _ = sound_at_48k(original, 6)
    checks = {
        "independent_physical_sound4_to5_copy_reconstruction_exact": reconstructed
        == old_copy.encoded_body,
        "new_sound7_is_exact_source_header_reference": sound_data(target, 6)
        == sound_data(original, 5)[:9],
        "source_full_buffer_preserved": sound_data(target, 5) == sound_data(original, 5),
        "all_non_sound7_plain_packets_preserved": excluding_destination_data(original, [6])
        == excluding_destination_data(target, [6]),
        "all_patterns_preserved": all(
            pattern_data(original, n) == pattern_data(target, n) for n in range(1, 17)
        ),
        "one_reference_packet_only": len(target.packets) - len(original.packets) == 1
        and len(target.encoded_body) - len(original.encoded_body) == 14,
        "expected_geometry": len(target.packets) == 952 and target.end_byte == 190229,
        "source_and_destination_previews_identical": np.array_equal(preview, original_preview),
        "dropping_only_new_reference_recovers_source": encode_packets(
            excluding_destination_data(target, [6])
        )
        == original.encoded_body,
        "source_artifact_preserved": source.to_bytes() == original_bytes,
    }
    if not all(checks.values()):
        raise ValueError("Reference-copy locality or geometry checks failed")
    directory.mkdir()
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    restore = directory / "restore.wav"
    write_bytes(restore, waveform)
    buffer = io.BytesIO()
    sf.write(buffer, preview, 48000, format="WAV", subtype="FLOAT")
    write_bytes(directory / "sound7-preview.wav", buffer.getvalue())
    recovered = decode_wav(restore, 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    decoded = decode_artifact(recovered)
    comparison = compare_artifacts(edited, recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        entire_target_body_after_wav_decode=decoded.encoded_body == target.encoded_body,
        entire_target_plain_packets_after_wav_decode=decoded.packets == target.packets,
        source_file_preserved=sha256_file(source_path) == acceptance["artifact_sha256"],
    )
    report = {
        "analysis_version": "generated-sound6-to7-reference-copy-probe-0.1",
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": acceptance["artifact_sha256"],
        "source_capture_sha256": acceptance["capture_sha256"],
        "source_body_sha256": acceptance["body_sha256"],
        "source_acceptance_sha256": sha256_file(acceptance_path),
        "restore_wav_sha256": sha256_file(restore),
        "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound7_reference_hex": sound_data(target, 6).hex(),
        "expected_sound6_payload_sha256": hashlib.sha256(sound_data(target, 5)).hexdigest(),
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "target_frame": frame_report(target),
        "preview": preview_report,
        "hardware_verified": False,
        "public_writer_scope_changed": False,
        "limits": [
            "This isolated probe inserts only the observed source header as a reference in existing empty Sound7, retaining owner5 under Sound6",
            "No full backing buffer is duplicated and all unrelated packets remain exact",
            "Only the reconstruction pair Sound4-to5 and candidate Sound6-to7 are supported; source must be unshared and destination empty",
            "Hardware acceptance is pending; shared-owner deletion, replacement, arbitrary copying and slot parameters remain unsupported",
        ],
    }
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Reference-copy waveform checks failed; outputs retained")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
