"""Build one research restore that carries many explicit raw edits at once.

This is a research tool, separate from the guarded public edit plans. Each
operation states exact raw bytes at a named location (pattern cell, footer or
opaque record byte), so many independent hypotheses can share one hardware round
trip. The spec binds the source artifact by hash. Unknown packets are preserved,
and the restore WAV only receives its final name after a strict software roundtrip.
A successful build says nothing about device acceptance or sound.
"""

import hashlib
import json
import os
from pathlib import Path

from .artifacts import json_bytes, sha256_file, write_bytes
from .formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    rebuild_labels,
)
from .formats.patterns import _replace_pattern_data, pattern_data
from .hardware.changes import describe_changes, summarize_change
from .modem.decode import decode_wav
from .modem.encode import encode_artifact
from .modem.roundtrip import compare_artifacts
from .modem.symbols import load_artifact

SPEC_SCHEMA = "po33.research-batch"
NO_EFFECT_FOOTER = bytes([0xFF]) * 8
REDECODE_THRESHOLD = 0.02
SPEC_KEYS = {
    "schema",
    "schema_version",
    "description",
    "source_artifact",
    "source_artifact_sha256",
    "operations",
    "playback_seconds",
    "observation_questions",
    "instructions",
}
OPERATION_KEYS = {
    "set_cell": {"pattern", "step", "sound", "primary", "auxiliary"},
    "clear_cell": {"pattern", "step", "sound"},
    "set_footer": {"pattern", "footer"},
    "clear_pattern": {"pattern"},
    "copy_pattern": {"source", "destination"},
    "set_record_byte": {"tag", "ordinal", "offset", "value"},
}


def _index(value, name, low=1, high=16):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer {low}..{high}")
    return value


def _hex(value, name, length):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a hex string")  # noqa: TRY004 -- invalid spec
    try:
        data = bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{name} is not valid hex") from exc
    if len(data) != length:
        raise ValueError(f"{name} must be exactly {length} bytes")
    return data


def _frame(packets):
    return decode_frame(encode_packets(packets), start=0)


def _cell_offsets(step, sound):
    return 48 * (step - 1) + 3 * (sound - 1), 768 + 16 * (step - 1) + (sound - 1)


def apply_operation(packets, operation):
    """Apply one raw research operation and return (packets, trace)."""
    if not isinstance(operation, dict) or operation.get("op") not in OPERATION_KEYS:
        raise ValueError(f"Unknown research operation: {operation!r}")
    name = operation["op"]
    arguments = set(operation) - {"op", "note"}
    if arguments != OPERATION_KEYS[name]:
        raise ValueError(f"{name} requires exactly {sorted(OPERATION_KEYS[name])}")
    frame = _frame(packets)
    if name == "set_record_byte":
        tag = operation["tag"]
        tag = int(tag, 16) if isinstance(tag, str) else tag
        _index(tag, "tag", 0, 0xFFFF)
        ordinal = _index(operation["ordinal"], "ordinal", 1, 4096)
        offset = _index(operation["offset"], "offset", 0, 254)
        value = _index(operation["value"], "value", 0, 255)
        matches = [i for i, p in enumerate(packets) if p.tag == tag]
        if len(matches) < ordinal:
            raise ValueError(f"No packet #{ordinal} with tag 0x{tag:04x}")
        index = matches[ordinal - 1]
        payload = bytearray(packets[index].payload)
        if offset >= len(payload):
            raise ValueError("Record offset is outside the payload")
        old = payload[offset]
        payload[offset] = value
        result = list(packets)
        result[index] = Packet(tag, bytes(payload))
        return tuple(result), {"packet_index": index, "old": old, "new": value}
    if name == "copy_pattern":
        source = _index(operation["source"], "source")
        destination = _index(operation["destination"], "destination")
        if source == destination:
            raise ValueError("copy_pattern needs two different patterns")
        data = pattern_data(frame, source)
        old = pattern_data(frame, destination)
        changed = sum(a != b for a, b in zip(old, data))
        return _replace_pattern_data(frame, destination, data), {"changed_bytes": changed}
    pattern = _index(operation["pattern"], "pattern")
    data = bytearray(pattern_data(frame, pattern))
    before = bytes(data)
    if name in ("set_cell", "clear_cell"):
        step = _index(operation["step"], "step")
        sound = _index(operation["sound"], "sound")
        p, a = _cell_offsets(step, sound)
        if name == "set_cell":
            primary = _hex(operation["primary"], "primary", 3)
            auxiliary = _hex(operation["auxiliary"], "auxiliary", 1)
        else:
            primary, auxiliary = bytes(3), bytes(1)
        trace = {"old_primary": before[p : p + 3].hex(), "old_auxiliary": f"{before[a]:02x}"}
        data[p : p + 3] = primary
        data[a] = auxiliary[0]
    elif name == "set_footer":
        footer = _hex(operation["footer"], "footer", 8)
        trace = {"old_footer": before[1024:].hex()}
        data[1024:] = footer
    else:  # clear_pattern
        occupied = [i for i in range(256) if any(before[3 * i : 3 * i + 3]) or before[768 + i]]
        trace = {"old_occupied_cells": len(occupied), "old_footer": before[1024:].hex()}
        data[:1024] = bytes(1024)
        data[1024:] = NO_EFFECT_FOOTER
    return _replace_pattern_data(frame, pattern, bytes(data)), trace


def load_spec(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    if not isinstance(spec, dict) or spec.get("schema") != SPEC_SCHEMA:
        raise ValueError(f"Spec schema must be {SPEC_SCHEMA}")
    if spec.get("schema_version") != 1:
        raise ValueError("Unsupported research batch schema version")
    unknown = set(spec) - SPEC_KEYS
    if unknown:
        raise ValueError(f"Unknown spec keys: {sorted(unknown)}")
    for key in ("source_artifact", "source_artifact_sha256", "operations", "description"):
        if key not in spec:
            raise ValueError(f"Spec requires {key}")
    if not isinstance(spec["operations"], list) or not spec["operations"]:
        raise ValueError("Spec requires a nonempty operations list")
    return spec


def build_batch(spec_path, out_dir, base_dir=None):
    """Compile a research batch spec into a fresh experiment folder."""
    spec_path, out_dir = Path(spec_path), Path(out_dir)
    if out_dir.exists() or not out_dir.parent.is_dir():
        raise ValueError("Batch output must be a fresh folder with an existing parent")
    spec_bytes = spec_path.read_bytes()
    spec = load_spec(spec_path)
    base = Path(base_dir) if base_dir else Path.cwd()
    source_path = base / spec["source_artifact"]
    source_hash = sha256_file(source_path)
    if source_hash != spec["source_artifact_sha256"]:
        raise ValueError("Source artifact hash differs from the spec")
    source = load_artifact(source_path)
    source_frame = decode_artifact(source)
    packets, traces = source_frame.packets, []
    for number, operation in enumerate(spec["operations"], 1):
        try:
            updated, trace = apply_operation(packets, operation)
        except ValueError as exc:
            raise ValueError(f"Operation {number}: {exc}") from exc
        traces.append({"operation": operation, "changed_body": updated != packets, **trace})
        packets = updated
    edited = rebuild_labels(source, packets)
    target = decode_artifact(edited)
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    if sha256_file(source_path) != source_hash:
        raise ValueError("Source artifact changed during the build")
    expected = describe_changes(source_frame, target)
    out_dir.mkdir()
    write_bytes(out_dir / "spec.json", spec_bytes)
    write_bytes(out_dir / "edited.symbols.npz", edited.to_bytes())
    pending = out_dir / "restore.unverified.wav"
    write_bytes(pending, waveform)
    redecoded = decode_wav(pending, REDECODE_THRESHOLD)
    write_bytes(out_dir / "redecoded.symbols.npz", redecoded.to_bytes())
    comparison = compare_artifacts(edited, redecoded)
    try:
        recovered = decode_artifact(redecoded)
        recovered_error = None
    except ValueError as exc:
        recovered, recovered_error = None, str(exc)
    checks = {
        "source_file_unchanged": sha256_file(source_path) == source_hash,
        "strict_phase_roundtrip": comparison["passed"],
        "exact_target_body_after_wav_decode": recovered is not None
        and recovered.encoded_body == target.encoded_body,
    }
    passed = all(checks.values())
    final = out_dir / ("restore.wav" if passed else "restore.FAILED.wav")
    os.replace(pending, final)
    target_hash = hashlib.sha256(target.encoded_body).hexdigest()
    report = {
        "analysis_version": "research-batch-build-0.1",
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "source_artifact_sha256": source_hash,
        "target_body_sha256": target_hash,
        "restore_wav": final.name,
        "restore_wav_sha256": sha256_file(final),
        "encoding": encoding,
        "operation_trace": traces,
        "expected_changes_from_source": expected,
        "strict_phase_roundtrip": comparison,
        "redecode_error": recovered_error,
        "no_op_operations": [i for i, t in enumerate(traces, 1) if not t["changed_body"]],
        "checks": checks,
        "passed": passed,
        "research_only": True,
        "hardware_verified": False,
    }
    write_bytes(out_dir / "software-validation.json", json_bytes(report))
    if not passed:
        raise ValueError("Research batch failed software checks; restore.FAILED.wav kept")
    experiment = {
        "experiment_id": out_dir.name,
        "kind": "research_batch",
        "description": spec["description"],
        "capture_status": "awaiting_hardware_session",
        "restore_file": "restore.wav",
        "expected_artifact": "edited.symbols.npz",
        "source_artifact": os.path.relpath(source_path, out_dir).replace("\\", "/"),
        "source_artifact_sha256": source_hash,
        "target_body_sha256": target_hash,
        "playback_seconds": spec.get("playback_seconds"),
        "observation_questions": spec.get("observation_questions"),
        "hardware_restore": {"status": "not_run"},
        "research_only": True,
    }
    write_bytes(out_dir / "experiment.json", json_bytes(experiment))
    lines = [
        f"# {out_dir.name}",
        "",
        spec["description"],
        "",
        "Run the guided session:",
        "",
        "```",
        f"python -m po33_re hw run {out_dir.as_posix()}",
        "```",
        "",
        f"Expected changes from the source ({expected['change_count']}):",
        "",
        *[f"- {summarize_change(c)}" for c in expected["changes"]],
    ]
    if spec.get("instructions"):
        lines[4:4] = [spec["instructions"], ""]
    write_bytes(out_dir / "instructions.md", ("\n".join(lines) + "\n").encode("utf-8"))
    return report
