"""Guarded plan compilation and a byte-exact replay of an accepted restore."""

import copy
import hashlib
import json
from itertools import pairwise
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.packets import decode_artifact, sound_data
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact


@pytest.fixture
def source_plan():
    root = Path(__file__).resolve().parents[1]
    source_path = (
        root / "experiments/event-013-b-sound3-start-min/derived/analysis-001/capture.symbols.npz"
    )
    plan_path = root / "experiments/replay-window-edit-001/plan.json"
    if not source_path.exists():
        pytest.skip("Reviewed genuine minimum artifact required")
    plan = json.loads(plan_path.read_text())
    assert sha256_file(source_path) == plan["source_artifact_sha256"]
    return source_path, plan_path, plan


@pytest.mark.capture
@pytest.mark.parametrize(
    "damage",
    ["version", "artifact_hash", "body_hash", "unknown_operation", "extra_argument", "step_list"],
)
def test_invalid_or_stale_plan_cannot_modify_source(source_plan, damage):
    source_path, _, original_plan = source_plan
    source = load_artifact(source_path)
    unchanged = source.to_bytes()
    plan = copy.deepcopy(original_plan)
    if damage == "version":
        plan["schema_version"] = True
    elif damage == "artifact_hash":
        plan["source_artifact_sha256"] = "0" * 64
    elif damage == "body_hash":
        plan["source_body_sha256"] = "0" * 64
    elif damage == "unknown_operation":
        plan["operations"] = [{"operation": "replace_raw_packets", "payload": "ff"}]
    elif damage == "extra_argument":
        plan["operations"][0]["start"] = 0
    else:
        plan["operations"] = [
            {"operation": "remove_sound_cell", "pattern": 1, "sound": 2, "steps": "9"}
        ]
    with pytest.raises(ValueError):
        apply_plan(source, sha256_file(source_path), plan)
    assert source.to_bytes() == unchanged


@pytest.mark.capture
def test_sequential_operations_preserve_other_cells_and_unknown_data(source_plan):
    source_path, _, original_plan = source_plan
    source = load_artifact(source_path)
    original = decode_artifact(source)
    plan = {
        **original_plan,
        "operations": [
            {
                "operation": "clone_sound_cell",
                "pattern": 1,
                "sound": 2,
                "source_step": 9,
                "target_steps": [1],
            },
            {"operation": "set_note_key", "pattern": 1, "sound": 3, "step": 5, "key": 7},
            {"operation": "remove_sound_cell", "pattern": 1, "sound": 2, "steps": [1]},
            {"operation": "set_sound_end", "sound": 3, "end": 39393},
        ],
    }
    edited, trace = apply_plan(source, sha256_file(source_path), plan)
    actual = decode_artifact(edited)
    before, after = pattern_data(original, 1), pattern_data(actual, 1)
    assert [(i, a, b) for i, (a, b) in enumerate(zip(before, after)) if a != b] == [(834, 241, 246)]
    assert [i for i, (a, b) in enumerate(zip(original.packets, actual.packets)) if a != b] == [
        7,
        375,
    ]
    assert sound_data(actual, 2).hex() == "a17a0000e199000000"
    assert sound_data(original, 0) == sound_data(actual, 0)
    assert len(trace) == 4
    assert all(a["after_body_sha256"] == b["before_body_sha256"] for a, b in pairwise(trace))
    assert hashlib.sha256(actual.encoded_body).hexdigest() == trace[-1]["after_body_sha256"]
    assert edited.metadata["hardware_verified"] is False


@pytest.mark.capture
def test_plan_compiler_replays_the_exact_accepted_restore_wav_and_refuses_overwrite(
    tmp_path, source_plan
):
    source_path, plan_path, _ = source_plan
    root = Path(__file__).resolve().parents[1]
    accepted = root / "experiments/generated-nonzero-trim-001/restore-sound3-window.wav"
    if not accepted.exists():
        pytest.skip("Previously accepted restore WAV required")
    output = tmp_path / "compiled"
    args = ["apply-edits", str(source_path), "--plan", str(plan_path), "--out-dir", str(output)]
    before = source_path.read_bytes()
    assert main(args) == 0
    assert (output / "restore.wav").read_bytes() == accepted.read_bytes()
    assert (
        sha256_file(output / "restore.wav")
        == "06b311337489a1176c80bc27172b343dc649ec2bd4c6880ad0d967470527949f"
    )
    assert (output / "plan.json").read_bytes() == plan_path.read_bytes()
    report = json.loads((output / "compile-report.json").read_text())
    assert report["passed"] and report["hardware_verified"] is False
    assert (
        report["target_body_sha256"]
        == "b3296f2ed7b3a74cedc79b8d89900e5128c7da1da0e2fed9839d1858412eddfe"
    )
    assert main(args) == 2
    assert source_path.read_bytes() == before


@pytest.mark.capture
def test_invalid_endpoint_produces_no_compile_directory(tmp_path, source_plan):
    source_path, _, original = source_plan
    plan = copy.deepcopy(original)
    plan["operations"][0]["end"] = 31503
    path = tmp_path / "invalid-plan.json"
    path.write_text(json.dumps(plan))
    output = tmp_path / "invalid-output"
    assert (
        main(["apply-edits", str(source_path), "--plan", str(path), "--out-dir", str(output)]) == 2
    )
    assert not output.exists()
