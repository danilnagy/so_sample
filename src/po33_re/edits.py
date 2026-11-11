"""Compile hash-bound JSON edit plans using only the existing bounded writers."""

import hashlib
import json
import os

from .artifacts import json_bytes, sha256_file, write_bytes
from .formats.drums import copy_calibrated_drum_slice, replace_calibrated_drum_slice_end
from .formats.effects import set_calibrated_pattern1_effect, set_step_effects
from .formats.filters import set_calibrated_sound3_filter
from .formats.globals import (
    set_calibrated_swing,
    set_calibrated_tempo,
    set_calibrated_tempo_preset,
    set_pattern_chain,
    set_selected_pattern,
    set_swing,
    set_tempo,
)
from .formats.lifecycle import copy_calibrated_melodic_reference, delete_calibrated_melodic_sound
from .formats.notes import set_step_parameters, set_unknown_bits
from .formats.packets import (
    decode_artifact,
    rebuild_labels,
    replace_calibrated_reference_end,
    replace_calibrated_reference_window,
    set_sample_window,
)
from .formats.patterns import (
    clone_drum_cell,
    clone_sound_cell,
    clone_step,
    copy_pattern,
    remove_drum_cell,
    remove_sound_cell,
    set_drum_notes,
    set_melodic_key,
    set_melodic_notes,
    set_notes,
)
from .formats.pitch import set_calibrated_sound3_pitch
from .formats.research import set_global_byte, set_raw_cell
from .formats.resonance import set_calibrated_sound3_resonance
from .formats.volume import set_calibrated_sound3_volume
from .modem.decode import decode_wav
from .modem.encode import encode_artifact
from .modem.roundtrip import compare_artifacts
from .modem.symbols import load_artifact

OPERATIONS = {
    "copy_pattern": (
        {"source_pattern", "destination_pattern"},
        lambda frame, op: copy_pattern(frame, op["source_pattern"], op["destination_pattern"]),
    ),
    "set_pattern_chain": (
        {"patterns"},
        lambda frame, op: set_pattern_chain(frame, op["patterns"]),
    ),
    "set_tempo_byte": (
        {"bpm"},
        lambda frame, op: set_tempo(frame, op["bpm"]),
    ),
    "set_swing_byte": (
        {"value"},
        lambda frame, op: set_swing(frame, op["value"]),
    ),
    "set_selected_pattern": (
        {"pattern"},
        lambda frame, op: set_selected_pattern(frame, op["pattern"]),
    ),
    "set_drum_notes": (
        {"pattern", "sound", "keys", "template_sound"},
        lambda frame, op: set_drum_notes(
            frame, op["pattern"], op["sound"], op["keys"], op["template_sound"]
        ),
    ),
    "set_melodic_notes_from": (
        {"pattern", "sound", "keys", "template_sound"},
        lambda frame, op: set_melodic_notes(
            frame, op["pattern"], op["sound"], op["keys"], op["template_sound"]
        ),
    ),
    "set_parameter_locks": (
        {"pattern", "sound", "parameter", "values"},
        lambda frame, op: set_step_parameters(
            frame, op["pattern"], op["sound"], op["parameter"], op["values"], allow_empty=True
        ),
    ),
    "set_note_unknown_bits": (
        {"pattern", "sound", "values"},
        lambda frame, op: set_unknown_bits(frame, op["pattern"], op["sound"], op["values"]),
    ),
    "set_sample_window": (
        {"sound", "start", "end"},
        lambda frame, op: set_sample_window(frame, op["sound"], op["start"], op["end"]),
    ),
    "set_raw_cell": (
        {"pattern", "step", "sound", "primary_hex", "auxiliary"},
        lambda frame, op: set_raw_cell(
            frame, op["pattern"], op["step"], op["sound"], op["primary_hex"], op["auxiliary"]
        ),
    ),
    "set_global_byte": (
        {"ordinal", "offset", "value"},
        lambda frame, op: set_global_byte(frame, op["ordinal"], op["offset"], op["value"]),
    ),
    "set_step_parameters": (
        {"pattern", "sound", "parameter", "values"},
        lambda frame, op: set_step_parameters(
            frame, op["pattern"], op["sound"], op["parameter"], op["values"]
        ),
    ),
    "set_notes": (
        {"pattern", "sound", "keys", "parameters"},
        lambda frame, op: set_notes(
            frame, op["pattern"], op["sound"], op["keys"], op["parameters"]
        ),
    ),
    "set_melodic_notes": (
        {"pattern", "sound", "keys"},
        lambda frame, op: set_melodic_notes(frame, op["pattern"], op["sound"], op["keys"]),
    ),
    "set_step_effects": (
        {"pattern", "effects"},
        lambda frame, op: set_step_effects(frame, op["pattern"], op["effects"]),
    ),
    "set_pattern1_effect": (
        {"effect"},
        lambda frame, op: set_calibrated_pattern1_effect(frame, op["effect"]),
    ),
    "set_sound3_resonance": (
        {"value"},
        lambda frame, op: set_calibrated_sound3_resonance(frame, op["value"]),
    ),
    "set_sound3_filter": (
        {"value"},
        lambda frame, op: set_calibrated_sound3_filter(frame, op["value"]),
    ),
    "set_sound3_pitch": (
        {"value"},
        lambda frame, op: set_calibrated_sound3_pitch(frame, op["value"]),
    ),
    "set_sound3_volume": (
        {"value"},
        lambda frame, op: set_calibrated_sound3_volume(frame, op["value"]),
    ),
    "set_swing": (
        {"value"},
        lambda frame, op: set_calibrated_swing(frame, op["value"]),
    ),
    "set_tempo": (
        {"bpm"},
        lambda frame, op: set_calibrated_tempo(frame, op["bpm"]),
    ),
    "set_tempo_preset": (
        {"bpm"},
        lambda frame, op: set_calibrated_tempo_preset(frame, op["bpm"]),
    ),
    "delete_melodic_sound": (
        {"sound"},
        lambda frame, op: delete_calibrated_melodic_sound(frame, op["sound"]),
    ),
    "copy_melodic_reference": (
        {"source_sound", "destination_sound"},
        lambda frame, op: copy_calibrated_melodic_reference(
            frame, op["source_sound"], op["destination_sound"]
        ),
    ),
    "clone_drum_cell": (
        {"pattern", "sound", "source_step", "target_steps"},
        lambda frame, op: clone_drum_cell(
            frame, op["pattern"], op["sound"], op["source_step"], op["target_steps"]
        ),
    ),
    "remove_drum_cell": (
        {"pattern", "sound", "steps"},
        lambda frame, op: remove_drum_cell(frame, op["pattern"], op["sound"], op["steps"]),
    ),
    "copy_drum_slice": (
        {"source_sound", "source_slice", "destination_sound", "destination_slice"},
        lambda frame, op: copy_calibrated_drum_slice(
            frame,
            op["source_sound"],
            op["source_slice"],
            op["destination_sound"],
            op["destination_slice"],
        ),
    ),
    "set_drum_slice_end": (
        {"sound", "slice", "end"},
        lambda frame, op: replace_calibrated_drum_slice_end(
            frame, op["sound"], op["slice"], op["end"]
        ),
    ),
    "set_sound_window": (
        {"sound", "start", "end"},
        lambda frame, op: replace_calibrated_reference_window(
            frame, op["sound"], op["start"], op["end"]
        ),
    ),
    "set_sound_end": (
        {"sound", "end"},
        lambda frame, op: replace_calibrated_reference_end(frame, op["sound"], op["end"]),
    ),
    "set_note_key": (
        {"pattern", "step", "sound", "key"},
        lambda frame, op: set_melodic_key(frame, op["pattern"], op["step"], op["sound"], op["key"]),
    ),
    "clone_sound_cell": (
        {"pattern", "sound", "source_step", "target_steps"},
        lambda frame, op: clone_sound_cell(
            frame, op["pattern"], op["sound"], op["source_step"], op["target_steps"]
        ),
    ),
    "remove_sound_cell": (
        {"pattern", "sound", "steps"},
        lambda frame, op: remove_sound_cell(frame, op["pattern"], op["sound"], op["steps"]),
    ),
    "clone_step": (
        {"pattern", "source_step", "target_steps"},
        lambda frame, op: clone_step(frame, op["pattern"], op["source_step"], op["target_steps"]),
    ),
}


def apply_plan(source, source_sha256, plan):
    required = {
        "schema",
        "schema_version",
        "source_artifact_sha256",
        "source_body_sha256",
        "operations",
    }
    if not isinstance(plan, dict) or set(plan) != required:
        raise ValueError(
            "Edit plan requires exactly the versioned schema, two source hashes and operations"
        )
    if (
        plan["schema"] != "po33.edit-plan"
        or type(plan["schema_version"]) is not int
        or plan["schema_version"] != 1
    ):
        raise ValueError("Unsupported edit plan schema")
    original = decode_artifact(source)
    if plan["source_artifact_sha256"] != source_sha256:
        raise ValueError(
            "Edit plan source artifact hash differs; regenerate the plan for this source"
        )
    if plan["source_body_sha256"] != hashlib.sha256(original.encoded_body).hexdigest():
        raise ValueError("Edit plan source native-body hash differs")
    if not isinstance(plan["operations"], list) or not plan["operations"]:
        raise ValueError("A nonempty operation list is required")
    for op in plan["operations"]:
        if (
            not isinstance(op, dict)
            or not isinstance(op.get("operation"), str)
            or op["operation"] not in OPERATIONS
        ):
            raise ValueError("Unsupported edit-plan operation")
        keys, _ = OPERATIONS[op["operation"]]
        if set(op) != keys | {"operation"}:
            raise ValueError(f"Unexpected or missing arguments for {op['operation']}")
        for name in ("steps", "target_steps"):
            if name in op and not isinstance(op[name], list):
                raise ValueError(f"{name} must be a list of step numbers")
    unchanged = source.to_bytes()
    working, trace = source, []
    for op in plan["operations"]:
        frame = decode_artifact(working)
        _, operation = OPERATIONS[op["operation"]]
        working = rebuild_labels(source, operation(frame, op))
        updated = decode_artifact(working)
        trace.append(
            {
                "operation": op,
                "before_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
                "after_body_sha256": hashlib.sha256(updated.encoded_body).hexdigest(),
            }
        )
    if source.to_bytes() != unchanged:
        raise ValueError("Source artifact changed while applying the plan")
    working.metadata["transformations"].append(
        {
            "kind": "bounded-edit-plan",
            "source_artifact_sha256": source_sha256,
            "operations": plan["operations"],
            "hardware_verified": False,
        }
    )
    return working, trace


def compile_edit_plan(source_path, plan_path, output_directory):
    if (
        output_directory.exists()
        or output_directory.is_symlink()
        or not output_directory.parent.is_dir()
    ):
        raise ValueError("Edit-plan output must be a fresh directory with an existing parent")
    source_hash = sha256_file(source_path)
    plan_bytes = plan_path.read_bytes()
    source = load_artifact(source_path)
    edited, trace = apply_plan(source, source_hash, json.loads(plan_bytes))
    target = decode_artifact(edited)
    waveform, encoding = encode_artifact(edited, rate=44100, amplitude=0.5)
    if sha256_file(source_path) != source_hash:
        raise ValueError("Source artifact changed before compilation completed")
    output_directory.mkdir()
    write_bytes(output_directory / "plan.json", plan_bytes)
    write_bytes(output_directory / "edited.symbols.npz", edited.to_bytes())
    # The restore only gets its final name after the waveform round trip passes.
    restore = output_directory / "restore.unverified.wav"
    write_bytes(restore, waveform)
    redecoded = decode_wav(restore, 0.02)
    write_bytes(output_directory / "redecoded.symbols.npz", redecoded.to_bytes())
    comparison = compare_artifacts(edited, redecoded)
    recovered = decode_artifact(redecoded)
    checks = {
        "source_file_unchanged": sha256_file(source_path) == source_hash,
        "all_packet_checksums": True,
        "strict_phase_roundtrip": comparison["passed"],
        "exact_target_body_after_wav_decode": recovered.encoded_body == target.encoded_body,
        "exact_target_packets_after_wav_decode": recovered.packets == target.packets,
    }
    final = output_directory / ("restore.wav" if all(checks.values()) else "restore.FAILED.wav")
    os.replace(restore, final)
    restore = final
    report = {
        "analysis_version": "bounded-edit-plan-compile-0.1",
        "source_artifact_sha256": source_hash,
        "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "operation_trace": trace,
        "target_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "restore_wav": restore.name,
        "restore_wav_sha256": sha256_file(restore),
        "encoding": encoding,
        "strict_phase_roundtrip": comparison,
        "checks": checks,
        "passed": all(checks.values()),
        "hardware_verified": False,
        "limits": [
            "Each operation retains its existing calibration and context guards; no arbitrary packet or JSON-view edits are imported",
            "Unknown packets are preserved through verified packet rebuilding; new combinations need appropriate hardware evidence",
        ],
    }
    write_bytes(output_directory / "compile-report.json", json_bytes(report))
    if not report["passed"]:
        raise ValueError("Compiled edit plan failed waveform or packet checks; report retained")
    return report
