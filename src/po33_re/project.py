"""Read-only research project export with exact raw packet preservation."""

import hashlib
import io

import soundfile as sf
from scipy.signal import resample_poly

from .artifacts import json_bytes, sha256_file, write_bytes
from .audio import inspect_wav
from .formats.packets import Packet, decode_artifact, encode_packets, sound_groups
from .formats.patterns import CALIBRATED_AUXILIARY_VALUES, pattern_data, patterns_report
from .formats.samples import (
    extract_calibrated_drum_slice_sound,
    extract_calibrated_window_sound,
    sound_at_48k,
)
from .modem.symbols import load_artifact


def packet_view(frame):
    return {
        "schema": "po33.native-packet-view",
        "schema_version": 1,
        "packet_count": len(frame.packets),
        "encoded_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "packets": [{"tag": p.tag, "payload_hex": p.payload.hex()} for p in frame.packets],
    }


def packets_from_view(view):
    """Check raw representation consistency; this does not authorize an edited restore."""
    try:
        if (
            view["schema"] != "po33.native-packet-view"
            or type(view["schema_version"]) is not int
            or view["schema_version"] != 1
        ):
            raise ValueError("Unsupported native packet view")
        if not isinstance(view["packets"], list) or type(view["packet_count"]) is not int:
            raise ValueError("Packet list and integer count required")
        packets = tuple(
            Packet(item["tag"], bytes.fromhex(item["payload_hex"])) for item in view["packets"]
        )
        body = encode_packets(packets)
        if (
            len(packets) != view["packet_count"]
            or hashlib.sha256(body).hexdigest() != view["encoded_body_sha256"]
        ):
            raise ValueError("Native packet view differs from its recorded count or body hash")
        return packets
    except (KeyError, TypeError) as exc:
        raise ValueError("Malformed native packet view") from exc


def _pattern_view(frame, report):
    events = []
    for row in report["nonzero_step_rows"]:
        for cell in row["nonzero_three_byte_cells"]:
            slot, primary, auxiliary = (
                cell["candidate_sound_slot"],
                cell["primary_hex"],
                cell["auxiliary_byte"],
            )
            key, drum_key = None, None
            if slot == 3 and primary == "0df883" and auxiliary in CALIBRATED_AUXILIARY_VALUES:
                key = (auxiliary & 15) + 1
            elif slot == 2 and primary == "0d2831" and auxiliary == 240:
                key = 1
            elif slot == 10 and primary == "0df883" and auxiliary in (0x10, 0x11):
                drum_key = {0x10: 1, 0x11: 2}[auxiliary]
            events.append(
                {
                    "step": row["step"],
                    "candidate_sound_slot": slot,
                    "primary_hex": primary,
                    "auxiliary_byte": auxiliary,
                    "calibrated_keyboard_key": key,
                    "calibrated_drum_slice_key": drum_key,
                }
            )
    return {
        **report,
        "data_hex": pattern_data(frame, report["pattern_slot"]).hex(),
        "observed_cells": events,
        "interpretation": "Melodic keys are identified only for locally calibrated Sound2/Sound3 pairs; exact Sound10 primary0df883/auxiliary10 or11 pairs identify recorded drum keys1/2; sample-reference mapping for Sound10/key2 and general upper-nibble meanings remain unverified",
    }


def drum_sound_view(frame, slot):
    """Group observed Sound9/10 blocks; retain other drum mappings as candidates.

    Selectors8..23 and24..39 belong to Sound9/10 in isolated copy controls.
    Sound9 keys1/2 map to selectors8/9; Sound10/key1 maps to24.
    Other keyboard/slot mappings are unverified.
    """
    if type(slot) is not int or not 9 <= slot <= 16:
        raise ValueError("A drum sound slot9..16 is required")
    groups = sound_groups(frame)
    first = 8 + 16 * (slot - 9)
    ids = list(range(first, first + 16))
    records, indices = [], []
    for candidate_key, selector in enumerate(ids, 1):
        packets = groups.get(selector, [])
        indices.extend(packets)
        data = b"".join(frame.packets[i].payload for i in packets)
        record = {
            "selector_id": selector,
            "candidate_slice_key": candidate_key,
            "keyboard_order_status": "unverified",
            "raw_packet_indices": packets,
            "data_payload_bytes": len(data),
            "data_hex": data.hex(),
        }
        if len(data) == 9:
            record["raw_reference_fields"] = {
                "first_u32le": int.from_bytes(data[:4], "little"),
                "second_u32le": int.from_bytes(data[4:8], "little"),
                "owner_id": data[8],
            }
        if slot == 9 and selector == 8:
            record.update(keyboard_key=1, keyboard_order_status="observed_key1_trim_control")
        elif slot == 9 and selector == 9:
            record.update(keyboard_key=2, keyboard_order_status="observed_key2_trim_control")
        elif slot == 10 and selector == 24:
            record.update(keyboard_key=1, keyboard_order_status="observed_key1_slice_copy_control")
        records.append(record)
    size = sum(r["data_payload_bytes"] for r in records)
    if slot in (9, 10):
        return {
            "sound_slot": slot,
            "selector_ids": ids,
            "selector_mapping_status": f"observed_sound{slot}_copy_block",
            "raw_packet_indices": indices,
            "data_payload_bytes": size,
            "slice_records": records,
            "preview_status": (
                "unsupported_drum_layout_preserved_raw" if indices else "no_sample_data_packets"
            ),
        }
    return {
        "sound_slot": slot,
        "candidate_selector_ids": ids,
        "selector_mapping_status": "inferred_other_drum_block_unverified",
        "candidate_raw_packet_indices": indices,
        "candidate_data_payload_bytes": size,
        "candidate_slice_records": records,
        "preview_status": "unverified_drum_slot_mapping_preserved_raw",
    }


def _preview_bytes(samples, cache):
    """Reuse identical mono previews, including their libsndfile header metadata."""
    key = (samples.dtype.str, samples.shape, hashlib.sha256(samples.tobytes()).digest())
    if key not in cache:
        buffer = io.BytesIO()
        sf.write(buffer, samples, 48000, format="WAV", subtype="FLOAT")
        cache[key] = buffer.getvalue()
    return cache[key]


def export_project(
    artifact_path,
    capture_path,
    output_directory,
    calibrated_windows=False,
    calibrated_drum_slices=False,
):
    """Export to a fresh folder after all input and representation checks pass."""
    if output_directory.exists() or output_directory.is_symlink():
        raise ValueError(
            "Project output must be a fresh directory; existing paths are never overwritten"
        )
    if not output_directory.parent.is_dir():
        raise ValueError("Project output parent directory does not exist")
    artifact = load_artifact(artifact_path)
    capture_bytes, artifact_bytes = capture_path.read_bytes(), artifact_path.read_bytes()
    capture_hash = hashlib.sha256(capture_bytes).hexdigest()
    artifact_hash = hashlib.sha256(artifact_bytes).hexdigest()
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError("Project source WAV does not match the decoded artifact")
    inspection = inspect_wav(capture_path)
    if inspection["source_sha256"] != capture_hash:
        raise ValueError("Source WAV changed while exporting")
    frame = decode_artifact(artifact)
    raw_view = packet_view(frame)
    if encode_packets(packets_from_view(raw_view)) != frame.encoded_body:
        raise ValueError("Raw packet view does not reproduce the complete native body")
    files = {
        "source/capture.wav": capture_bytes,
        "source/capture.symbols.npz": artifact_bytes,
        "source/native-body.bin": frame.encoded_body,
        "source/packets.json": json_bytes(raw_view),
    }
    pattern_index = []
    for pattern in patterns_report(frame)["patterns"]:
        name = f"patterns/{pattern['pattern_slot']:02}.json"
        files[name] = json_bytes(_pattern_view(frame, pattern))
        pattern_index.append(
            {
                "pattern_slot": pattern["pattern_slot"],
                "file": name,
                "payload_sha256": pattern["payload_sha256"],
            }
        )
    groups = sound_groups(frame)
    sounds, previews, drum_previews = [], [], []
    preview_cache = {}
    for slot in range(1, 17):
        if slot > 8:
            record = drum_sound_view(frame, slot)
            if calibrated_drum_slices and slot in (9, 10):
                preview_keys = []
                for slice_key in (1, 2) if slot == 9 else (1,):
                    try:
                        samples, sample_report = extract_calibrated_drum_slice_sound(
                            frame, slot, slice_key
                        )
                    except ValueError as exc:
                        record["calibrated_drum_preview_reason"] = str(exc)
                    else:
                        samples = resample_poly(samples, 256, 125)
                        name = f"samples/{slot:02}-slice-{slice_key:02}.wav"
                        files[name] = _preview_bytes(samples, preview_cache)
                        record["slice_records"][slice_key - 1].update(
                            **sample_report,
                            preview_status="exported_calibrated_drum_slice",
                            preview_file=name,
                            preview_pcm_subtype="FLOAT",
                            export_sample_rate_hz=48000,
                            export_frames=len(samples),
                        )
                        drum_previews.append(
                            {"sound_slot": slot, "slice_key": slice_key, "file": name}
                        )
                        preview_keys.append(slice_key)
                if preview_keys:
                    record.update(
                        preview_status="exported_calibrated_drum_slices",
                        preview_slice_keys=preview_keys,
                    )
            sounds.append(record)
            continue
        indices = groups.get(slot - 1, [])
        record = {
            "sound_slot": slot,
            "raw_packet_indices": indices,
            "data_payload_bytes": sum(len(frame.packets[i].payload) for i in indices),
        }
        if not indices:
            record["preview_status"] = "no_sample_data_packets"
        else:
            try:
                samples, sample_report = sound_at_48k(frame, slot)
                preview_status = "exported_zero_start_melodic"
            except ValueError as exc:
                record.update(preview_status="unsupported_layout_preserved_raw", reason=str(exc))
                if not calibrated_windows or slot != 3:
                    sounds.append(record)
                    continue
                try:
                    samples, sample_report = extract_calibrated_window_sound(frame, slot)
                except ValueError as window_error:
                    record["calibrated_window_reason"] = str(window_error)
                    sounds.append(record)
                    continue
                samples = resample_poly(samples, 256, 125)
                sample_report.update(export_sample_rate_hz=48000, export_frames=len(samples))
                preview_status = "exported_calibrated_fixed_start_window"
                record.pop("reason", None)
            if samples is not None:
                name = f"samples/{slot:02}.wav"
                files[name] = _preview_bytes(samples, preview_cache)
                record.update(
                    preview_status=preview_status,
                    preview_file=name,
                    preview_pcm_subtype="FLOAT",
                    **sample_report,
                )
                previews.append(slot)
        sounds.append(record)
    files["sounds.json"] = json_bytes(
        {"schema": "po33.sound-view", "schema_version": 2, "sounds": sounds}
    )
    files["project.json"] = json_bytes(
        {
            "schema": "po33.research-project",
            "schema_version": 1,
            "read_only": True,
            "source": {
                "capture_file": "source/capture.wav",
                "capture_sha256": capture_hash,
                "artifact_file": "source/capture.symbols.npz",
                "artifact_sha256": artifact_hash,
                "decoder_version": artifact.metadata["decoder_version"],
                "transport_extent": artifact.metadata.get(
                    "transport_extent", "see_source_artifact"
                ),
                "transformations": artifact.metadata.get("transformations", []),
            },
            "native_frame": {
                "packets_file": "source/packets.json",
                "body_file": "source/native-body.bin",
                "body_sha256": raw_view["encoded_body_sha256"],
                "packet_count": len(frame.packets),
                "frame_end_byte": frame.end_byte,
            },
            "patterns": pattern_index,
            "sounds_file": "sounds.json",
            "preview_sound_slots": previews,
            "preview_drum_slices": drum_previews,
            "calibrated_windows_requested": calibrated_windows,
            "calibrated_drum_slices_requested": calibrated_drum_slices,
            "limits": [
                "This is a read-only research export; edited JSON is not an import or restore interface",
                "All unknown packets, cells and parameters are retained exactly in source/packets.json and the copied source artifact",
                "Sample previews use nominal-rate extraction without applying sequencer pitch; raw codes remain in the packet view",
                "Calibrated-window previews require explicit opt-in and support only the two observed Sound3 starts; endpoint inclusivity remains unresolved",
                "Sound9 selector8..23 records are grouped raw; only keys1/2 have calibrated audio previews, requiring explicit opt-in and their fixed-start context guards",
                "Sound10 key1 maps to selector24; opt-in preview supports only its two accepted copied windows under local context guards; other keys remain unverified",
                "Drum preview uses an unpitched raw-code half-open selection; other drum keyboard/slot mappings and exact device endpoint inclusivity remain unverified",
                "Other nonzero starts, allocation and unknown note parameters are not interpreted",
                "native-body.bin contains the encoded native frame body, excluding acquisition and post-frame carrier; it is not a complete capture or state image",
            ],
        }
    )
    if sha256_file(capture_path) != capture_hash or sha256_file(artifact_path) != artifact_hash:
        raise ValueError("Source input changed before project export could complete")
    report = {
        "analysis_version": "read-only-project-export-0.10",
        "source_capture_sha256": capture_hash,
        "source_artifact_sha256": artifact_hash,
        "native_body_sha256": raw_view["encoded_body_sha256"],
        "pattern_count": 16,
        "preview_sound_slots": previews,
        "preview_drum_slices": drum_previews,
        "calibrated_windows_requested": calibrated_windows,
        "calibrated_drum_slices_requested": calibrated_drum_slices,
        "checks": {
            "source_identity": True,
            "all_native_checksums": True,
            "exact_packet_view_roundtrip": True,
            "source_files_unchanged": True,
        },
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in files.items()
        },
        "read_only": True,
        "hardware_verified": False,
    }
    output_directory.mkdir()
    for name, data in files.items():
        path = output_directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        write_bytes(path, data)
    write_bytes(output_directory / "export-report.json", json_bytes(report))
    return report
