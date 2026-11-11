"""Test a nine-page Sound6 buffer without assuming allocation rounds to8192 codes."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
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


def create_nine_page_sound6(frame, template):
    """Append one zero4096-code page to the exact observed eight-page Sound6."""
    groups, old_groups = sound_groups(frame), sound_groups(template)
    if 5 not in groups or groups[5] or 6 not in groups or groups[6]:
        raise ValueError("Both Sound6 and Sound7 must be empty")
    data = sound_data(template, 5)
    if len(data) != 32777 or data[:9].hex() != "00000000c078000005":
        raise ValueError("Expected the observed eight-page self-owned Sound6 template")
    old_indices = old_groups[5]
    if (
        old_indices != list(range(old_indices[0], old_indices[-1] + 1))
        or [len(template.packets[i].payload) for i in old_indices]
        != [255] * 16 + [25] + ([255] * 16 + [16]) * 7
    ):
        raise ValueError("Expected the observed ordered4096-code page geometry")
    if excluding_destination_data(frame, [5]) != excluding_destination_data(template, [5]):
        raise ValueError("Source and template differ on unrelated packets")
    chunks = (
        tuple(template.packets[i] for i in old_indices)
        + (Packet(0xEF78, bytes(255)),) * 16
        + (Packet(0xEF78, bytes(16)),)
    )
    index = next(i for i, packet in enumerate(frame.packets) if packet == Packet(0x68B5, b"\x05"))
    return frame.packets[: index + 1] + chunks + frame.packets[index + 1 :]


def run(directory):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with existing parent required")
    baseline = root / "experiments/event-027-b-delete-unshared-sound7"
    evidence_path = baseline / "native-evidence-001.json"
    evidence = json.loads(evidence_path.read_text())
    template_dir = root / "experiments/edited-sound6-create-001"
    template_evidence = json.loads((template_dir / "hardware-acceptance-001.json").read_text())
    source_path = baseline / "derived/analysis-001/capture.symbols.npz"
    template_path = template_dir / "derived/analysis-001/capture.symbols.npz"
    if (
        not evidence["hardware_observed"]
        or not template_evidence["hardware_verified"]
        or sha256_file(source_path) != evidence["artifact_sha256"]
        or sha256_file(template_path) != template_evidence["artifact_sha256"]
        or sha256_file(baseline / "capture.wav") != evidence["capture_sha256"]
    ):
        raise ValueError("Matching native deletion and hardware creation evidence required")
    source = load_artifact(source_path)
    original, template = decode_artifact(source), decode_artifact(load_artifact(template_path))
    if hashlib.sha256(original.encoded_body).hexdigest() != evidence["body_sha256"]:
        raise ValueError("Baseline body differs from reviewed deletion")
    original_bytes = source.to_bytes()
    edited = rebuild_labels(source, create_nine_page_sound6(original, template))
    edited.metadata["transformations"].append(
        {
            "kind": "odd-nine-page-sound6-capacity-probe",
            "capacity_codes": 36864,
            "source_artifact_sha256": evidence["artifact_sha256"],
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    preview, preview_report = sound_at_48k(target, 6)
    template_preview, _ = sound_at_48k(template, 6)
    data, old = sound_data(target, 5), sound_data(template, 5)
    checks = {
        "nine_page_capacity": len(data) == 36873
        and (len(data) - 9) % 4096 == 0
        and (len(data) - 9) % 8192 != 0,
        "entire_old_record_is_exact_prefix": data[: len(old)] == old,
        "one_added_page_is_zero": data[len(old) :] == bytes(4096),
        "logical_preview_unchanged": np.array_equal(preview, template_preview),
        "all_non_sound6_plain_packets_preserved": excluding_destination_data(original, [5])
        == excluding_destination_data(target, [5]),
        "all_patterns_preserved": all(
            pattern_data(original, n) == pattern_data(target, n) for n in range(1, 17)
        ),
        "sound7_stays_empty": not sound_groups(target)[6],
        "expected_geometry": len(target.packets) == 968 and target.end_byte == 194396,
        "source_artifact_preserved": source.to_bytes() == original_bytes,
    }
    if not all(checks.values()):
        raise ValueError("Odd-page candidate locality or geometry checks failed")
    directory.mkdir()
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    restore = directory / "restore.wav"
    write_bytes(restore, waveform)
    buffer = io.BytesIO()
    sf.write(buffer, preview, 48000, format="WAV", subtype="FLOAT")
    write_bytes(directory / "sound6-preview.wav", buffer.getvalue())
    recovered = decode_wav(restore, 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    decoded = decode_artifact(recovered)
    comparison = compare_artifacts(edited, recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        entire_target_body_after_wav_decode=decoded.encoded_body == target.encoded_body,
        entire_target_plain_packets_after_wav_decode=decoded.packets == target.packets,
        source_file_preserved=sha256_file(source_path) == evidence["artifact_sha256"],
        template_file_preserved=sha256_file(template_path) == template_evidence["artifact_sha256"],
    )
    report = {
        "analysis_version": "odd-nine-page-sound6-capacity-candidate-0.1",
        "source_artifact": source_path.relative_to(root).as_posix(),
        "source_artifact_sha256": evidence["artifact_sha256"],
        "source_capture_sha256": evidence["capture_sha256"],
        "source_body_sha256": evidence["body_sha256"],
        "source_native_evidence_sha256": sha256_file(evidence_path),
        "template_artifact": template_path.relative_to(root).as_posix(),
        "template_artifact_sha256": template_evidence["artifact_sha256"],
        "restore_wav_sha256": sha256_file(restore),
        "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound6_payload_sha256": hashlib.sha256(data).hexdigest(),
        "expected_sound6_header_hex": data[:9].hex(),
        "capacity_codes": 36864,
        "page_count4096": 9,
        "logical_endpoint": 30912,
        "zero_tail_codes": 5952,
        "total_backing_capacity_codes": 167936,
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "target_frame": frame_report(target),
        "preview": preview_report,
        "hardware_verified": False,
        "public_writer_scope_changed": False,
        "limits": [
            "This experiment varies serialized capacity only by adding one unused zero4096-code page to a previously hardware-tested sample",
            "A matching nine-page recapture, rounding to a different capacity and dropping the unused page are separate outcomes",
            "The original32768 codes and30912-code window are pinned independently of the extra page",
            "Native serialized capacity does not measure firmware physical allocation units or RAM addresses",
            "No public allocator or supported deletion/resize scope is expanded by this pending test",
        ],
    }
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Odd-page waveform checks failed; outputs retained")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
