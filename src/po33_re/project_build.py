"""Build a complete PO-33 project from a description, using only verified writers.

A project spec is a dict:

    {
      "tempo": 100, "swing": 4, "chain": [1, 2],
      "melodic": {"8": "path/to/tone.wav"},            # slot -> WAV (mono or stereo PCM)
      "drums": {"9": ["hit01.wav", ..., "hit16.wav"]},  # slot -> 16 WAVs, key 1 first
      "patterns": {
        "1": {
          "notes": {"8": [1, null, 5, ...], "13": [1, null, ...]},   # sound -> 16 keys
          "parameters": {"8": {"pitch": 13, "volume": 36, "filter": 63, "resonance": 1}},
          "locks": {"8": {"filter": [null, 24, ...]}},  # optional per-step locks
          "effects": [null, 7, ...]                     # optional 16 FX keys
        }
      }
    }

Every pattern listed is written in full: sounds not named are cleared. Sample imports run
first, each as its own staged import, then one hash-bound edit plan applies the pattern,
chain, tempo and swing writes. Hardware behaviour of each writer is documented in
docs/edit-plans.md; the end-to-end build is under docs/project-build-control.md.
"""

import hashlib
import json
from pathlib import Path

from .artifacts import json_bytes, sha256_file, write_bytes
from .drum_import import compile_drum_kit_import
from .edits import compile_edit_plan
from .formats.globals import MAX_SWING, MAX_TEMPO_BPM, MIN_SWING, MIN_TEMPO_BPM
from .formats.packets import decode_artifact
from .modem.symbols import load_artifact
from .sample_import import DEVICE_SAMPLE_LIMIT, compile_sample_import

DEFAULT_PARAMETERS = {"pitch": 13, "volume": 36, "filter": 63, "resonance": 1}
MELODIC_MAX_FRAMES = 4 * 23438  # 4.0 s, the longest melodic import verified


def pattern_operations(number, spec):
    """Edit-plan operations writing one pattern in full."""
    notes = {int(k): v for k, v in spec.get("notes", {}).items()}
    parameters = {int(k): v for k, v in spec.get("parameters", {}).items()}
    locks = {int(k): v for k, v in spec.get("locks", {}).items()}
    operations = []
    for sound in range(1, 17):
        keys = notes.get(sound, [None] * 16)
        operations.append(
            {
                "operation": "set_notes",
                "pattern": number,
                "sound": sound,
                "keys": keys,
                "parameters": {**DEFAULT_PARAMETERS, **parameters.get(sound, {})},
            }
        )
        for parameter, values in locks.get(sound, {}).items():
            operations.append(
                {
                    "operation": "set_parameter_locks",
                    "pattern": number,
                    "sound": sound,
                    "parameter": parameter,
                    "values": values,
                }
            )
    operations.append(
        {
            "operation": "set_step_effects",
            "pattern": number,
            "effects": spec.get("effects", [None] * 16),
        }
    )
    return operations


def build_project(source_path, spec, output_directory):
    """Import the spec's samples, then compile the pattern and global writes; return a report."""
    output_directory = Path(output_directory)
    if output_directory.exists():
        raise ValueError("Project build output must be a fresh directory")
    tempo, swing = spec.get("tempo"), spec.get("swing")
    if tempo is not None and not MIN_TEMPO_BPM <= tempo <= MAX_TEMPO_BPM:
        raise ValueError(f"Tempo must be {MIN_TEMPO_BPM}..{MAX_TEMPO_BPM}")
    if swing is not None and not MIN_SWING <= swing <= MAX_SWING:
        raise ValueError(f"Swing must be {MIN_SWING}..{MAX_SWING}")
    output_directory.mkdir()
    current, imports = Path(source_path), []
    for slot, wav in sorted(spec.get("melodic", {}).items(), key=lambda kv: int(kv[0])):
        stage = output_directory / f"import-sound{int(slot)}"
        report = compile_sample_import(
            current,
            Path(wav),
            stage,
            int(slot),
            None,
            None,
            (int(slot),),
            DEVICE_SAMPLE_LIMIT,
            max_frames=MELODIC_MAX_FRAMES,
            page_capacity=True,
            replace_borrowed=True,
        )
        imports.append(
            {
                "slot": int(slot),
                "kind": "melodic",
                "stage": stage.name,
                "allocation": report["allocation"],
            }
        )
        current = stage / "edited.symbols.npz"
    for slot, wavs in sorted(spec.get("drums", {}).items(), key=lambda kv: int(kv[0])):
        stage = output_directory / f"import-sound{int(slot)}"
        report = compile_drum_kit_import(
            current,
            [Path(w) for w in wavs],
            stage,
            int(slot),
            allowed_slots=(int(slot),),
            total_limit=DEVICE_SAMPLE_LIMIT,
        )
        imports.append(
            {
                "slot": int(slot),
                "kind": "drum",
                "stage": stage.name,
                "allocation": report["allocation"],
            }
        )
        current = stage / "edited.symbols.npz"
    operations = []
    for number, pattern in sorted(spec.get("patterns", {}).items(), key=lambda kv: int(kv[0])):
        operations += pattern_operations(int(number), pattern)
    if spec.get("chain"):
        operations.append({"operation": "set_pattern_chain", "patterns": spec["chain"]})
    if tempo is not None:
        operations.append({"operation": "set_tempo_byte", "bpm": tempo})
    if swing is not None:
        operations.append({"operation": "set_swing_byte", "value": swing})
    frame = decode_artifact(load_artifact(current))
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(current),
        "source_body_sha256": hashlib.sha256(frame.encoded_body).hexdigest(),
        "operations": operations,
    }
    plan_path = output_directory / "plan.json"
    write_bytes(plan_path, json_bytes(plan))
    compiled = output_directory / "compiled"
    report = compile_edit_plan(current, plan_path, compiled)
    summary = {
        "analysis_version": "project-build-0.1",
        "source_artifact_sha256": sha256_file(Path(source_path)),
        "spec_sha256": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
        "imports": imports,
        "plan_sha256": sha256_file(plan_path),
        "compiled": compiled.name,
        "target_body_sha256": report["target_body_sha256"],
        "restore_wav": str(compiled / report["restore_wav"]),
        "restore_wav_sha256": report["restore_wav_sha256"],
        "passed": report["passed"],
        "hardware_verified": False,
    }
    write_bytes(output_directory / "build-report.json", json_bytes(summary))
    return summary
