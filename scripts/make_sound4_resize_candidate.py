"""Build bounded unshared Sound4 grow/shrink probes from two device layouts."""

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.analysis.playback import measure_tone
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
from po33_re.formats.patterns import pattern_data
from po33_re.formats.samples import encode_signed_mulaw, sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data


def resize_unshared_sound4_from_template(frame, template, codes):
    """Only transitions between32768/end30912 and73728/end72128 self-owner3.

    Reuse the exact target device packet geometry. Reject shared owners and any
    unrelated state mismatch; this research probe is not a general allocator.
    """
    if not isinstance(codes, np.ndarray) or codes.dtype != np.uint8 or codes.ndim != 1:
        raise ValueError("One-dimensional uint8 replacement codes required")
    layouts = {32768: "00000000c078000003", 73728: "00000000c019010003"}
    source_capacity = len(sound_data(frame, 3)) - 9
    target_capacity = len(sound_data(template, 3)) - 9
    if {source_capacity, target_capacity} != set(layouts) or len(codes) != target_capacity:
        raise ValueError("Only opposite observed32768/73728-code layouts are supported")
    for current, capacity in ((frame, source_capacity), (template, target_capacity)):
        data = sound_data(current, 3)
        groups = sound_groups(current)
        if data[:9].hex() != layouts[capacity]:
            raise ValueError("Expected the exact observed Sound4 owner layout")
        referrers = [
            key
            for key, indices in groups.items()
            if indices and len(record := sound_data(current, key)) >= 9 and record[8] == 3
        ]
        if referrers != [3]:
            raise ValueError("Sound4 backing owner must be unshared")
        indices = groups[3]
        lengths = [len(current.packets[i].payload) for i in indices]
        if indices != list(range(indices[0], indices[-1] + 1)) or lengths != (
            [255] * 16 + [25] + ([255] * 16 + [16]) * (capacity // 4096 - 1)
        ):
            raise ValueError("Expected contiguous observed4096-code page packet geometry")
    if excluding_destination_data(frame, [3]) != excluding_destination_data(template, [3]):
        raise ValueError("Source and resize template must agree on every unrelated packet")
    replacement = sound_data(template, 3)[:9] + codes.tobytes()
    chunks, offset = [], 0
    for index in sound_groups(template)[3]:
        length = len(template.packets[index].payload)
        chunks.append(Packet(0xEF78, replacement[offset : offset + length]))
        offset += length
    if offset != len(replacement):
        raise ValueError("Template geometry does not cover the replacement")
    indices = sound_groups(frame)[3]
    return frame.packets[: indices[0]] + tuple(chunks) + frame.packets[indices[-1] + 1 :]


def run(directory, direction="grow"):
    root = Path(__file__).resolve().parents[1]
    if directory.exists() or directory.is_symlink() or not directory.parent.is_dir():
        raise ValueError("Fresh output directory with an existing parent required")
    if direction not in ("grow", "shrink"):
        raise ValueError("Direction must be grow or shrink")
    if direction == "grow":
        evidence_path = root / "experiments/unshared-sound4-shrink-results-001.json"
        template_evidence_path = root / "experiments/shared-sound4-rerecord-results-001.json"
        template_path = (
            root
            / "experiments/event-024-b-rerecord-shared-sound4/derived/analysis-001/capture.symbols.npz"
        )
    else:
        evidence_path = (
            root / "experiments/edited-sound4-growth-001/hardware-recapture-results-001.json"
        )
        template_evidence_path = root / "experiments/unshared-sound4-shrink-results-001.json"
        template_path = (
            root
            / "experiments/event-025-b-rerecord-unshared-sound4-short/derived/analysis-001/capture.symbols.npz"
        )
        acceptance = json.loads(
            (root / "experiments/edited-sound4-growth-001/hardware-acceptance-001.json").read_text()
        )
        if not acceptance["hardware_verified"] or acceptance[
            "recapture_results_sha256"
        ] != sha256_file(evidence_path):
            raise ValueError("Verified generated growth required before shrink probe")
    evidence, template_evidence = (
        json.loads(evidence_path.read_text()),
        json.loads(template_evidence_path.read_text()),
    )
    source_path = Path(evidence["artifact_path"])
    source_reviewed = (
        evidence["control_passed"]
        and evidence["hypothesis_checks"]["new_sound4_backing_capacity_shrinks"]
        and evidence["hypothesis_checks"]["all_non_sound4_plain_packets_unchanged"]
        if direction == "grow"
        else evidence["passed"] and all(evidence["checks"].values())
    )
    if (
        not source_reviewed
        or not template_evidence["control_passed"]
        or sha256_file(source_path) != evidence["artifact_sha256"]
        or sha256_file(template_path) != template_evidence["artifact_sha256"]
    ):
        raise ValueError("Matching reviewed shrink and growth evidence required")
    source = load_artifact(source_path)
    before_bytes = source.to_bytes()
    original, template = decode_artifact(source), decode_artifact(load_artifact(template_path))
    if (
        hashlib.sha256(original.encoded_body).hexdigest()
        != evidence["native_frame"]["encoded_body_sha256"]
        or source.metadata["source_sha256"] != evidence["capture_sha256"]
    ):
        raise ValueError("Source native body or capture identity differs")
    rate = 23437.5
    capacity, endpoint, frequency = (
        (73728, 72128, 1750) if direction == "grow" else (32768, 30912, 2250)
    )
    tone = 0.25 * np.sin(2 * np.pi * frequency * np.arange(endpoint) / rate)
    fade = np.linspace(0, 1, 117)
    tone[:117] *= fade
    tone[-117:] *= fade[::-1]
    codes = np.zeros(capacity, dtype=np.uint8)
    codes[:endpoint] = encode_signed_mulaw(tone)
    edited = rebuild_labels(source, resize_unshared_sound4_from_template(original, template, codes))
    edited.metadata["transformations"].append(
        {
            "kind": f"observed-layout-unshared-sound4-{direction}-probe",
            "source_artifact_sha256": evidence["artifact_sha256"],
            "template_artifact_sha256": template_evidence["artifact_sha256"],
            "capacity_codes": capacity,
            "endpoint": endpoint,
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    checks = {
        "reconstruction_with_original_template_codes_is_exact": encode_packets(
            resize_unshared_sound4_from_template(
                original, template, np.frombuffer(sound_data(template, 3)[9:], dtype=np.uint8)
            )
        )
        == template.encoded_body,
        "all_non_sound4_plain_packets_preserved": excluding_destination_data(original, [3])
        == excluding_destination_data(target, [3]),
        "all_patterns_preserved": all(
            pattern_data(original, n) == pattern_data(target, n) for n in range(1, 17)
        ),
        "sound5_entire_record_preserved": sound_data(original, 4) == sound_data(target, 4),
        "source_artifact_preserved": source.to_bytes() == before_bytes,
        "observed_target_geometry": len(target.packets) == len(template.packets)
        and target.end_byte == template.end_byte,
    }
    if not all(checks.values()):
        raise ValueError("Candidate reconstruction or locality checks failed")
    preview, preview_report = sound_at_48k(target, 4)
    # This detector estimates its noise floor from quiet portions. The candidate
    # deliberately fills its window, so add explicit analysis-only silence.
    fit = measure_tone(np.pad(preview, (0, 60000)), 48000)
    directory.mkdir()
    write_bytes(directory / "edited.symbols.npz", edited.to_bytes())
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    restore_path = directory / "restore.wav"
    write_bytes(restore_path, waveform)
    buffer = io.BytesIO()
    sf.write(buffer, preview, 48000, format="WAV", subtype="FLOAT")
    write_bytes(directory / "sound4-preview.wav", buffer.getvalue())
    recovered = decode_wav(restore_path, 0.02)
    write_bytes(directory / "redecoded.symbols.npz", recovered.to_bytes())
    decoded = decode_artifact(recovered)
    comparison = compare_artifacts(edited, recovered)
    checks.update(
        strict_phase_roundtrip=comparison["passed"],
        entire_target_body_after_wav_decode=decoded.encoded_body == target.encoded_body,
        entire_target_plain_packets_after_wav_decode=decoded.packets == target.packets,
        generated_tone_fit=frequency - 1 < fit["dominant_frequency_hz"] < frequency + 1,
        source_file_preserved=sha256_file(source_path) == evidence["artifact_sha256"],
        template_file_preserved=sha256_file(template_path) == template_evidence["artifact_sha256"],
    )
    report = {
        "analysis_version": "observed-layout-unshared-sound4-resize-probe-0.2",
        "direction": direction,
        "source_artifact_sha256": evidence["artifact_sha256"],
        "source_capture_sha256": evidence["capture_sha256"],
        "source_body_sha256": hashlib.sha256(original.encoded_body).hexdigest(),
        "template_artifact_sha256": template_evidence["artifact_sha256"],
        "source_evidence_sha256": sha256_file(evidence_path),
        "template_evidence_sha256": sha256_file(template_evidence_path),
        "restore_wav_sha256": sha256_file(restore_path),
        "edited_artifact_sha256": sha256_file(directory / "edited.symbols.npz"),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound4_payload_sha256": hashlib.sha256(sound_data(target, 3)).hexdigest(),
        "expected_sound4_header_hex": sound_data(target, 3)[:9].hex(),
        "expected_sound5_payload_sha256": hashlib.sha256(sound_data(target, 4)).hexdigest(),
        "checks": checks,
        "passed": all(checks.values()),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "target_frame": frame_report(target),
        "preview": preview_report,
        "independently_fitted_tone": fit,
        "tone_measurement_only_trailing_zero_frames": 60000,
        "generated_frequency_hz": frequency,
        "nominal_tone_duration_seconds": endpoint / rate,
        "hardware_verified": False,
        "public_writer_scope_changed": False,
        "limits": [
            "This probe resizes only unshared Sound4 between two observed allocations and reuses the exact target header and chunk lengths",
            "No general allocation rounding, memory limit, new slot, deletion or shared-owner mutation is implemented",
            f"A generated{frequency}Hz tone fills the logical window;{capacity - endpoint} tail codes are intentionally zero in the generated replacement",
            "Waveform checks are software-only; hardware acceptance and a matching recapture are pending",
        ],
    }
    write_bytes(directory / "software-validation.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Candidate waveform checks failed; outputs retained")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--direction", choices=("grow", "shrink"), default="grow")
    args = parser.parse_args()
    run(args.out_dir, args.direction)


if __name__ == "__main__":
    main()
