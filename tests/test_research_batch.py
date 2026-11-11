import json

import pytest
from synthetic_capture import artifact_from_packets, pattern_bytes, synthetic_packets

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from po33_re.research_batch import apply_operation, build_batch

NOTE = ("0e0981", 0xF0)


@pytest.fixture
def source(tmp_path):
    packets = synthetic_packets(
        patterns={1: pattern_bytes([(1, 3, *NOTE), (5, 2, "0d2831", 0xF0)])}
    )
    path = tmp_path / "source.symbols.npz"
    path.write_bytes(artifact_from_packets(packets).to_bytes())
    return path


def write_spec(tmp_path, source, operations, **extra):
    spec = {
        "schema": "po33.research-batch",
        "schema_version": 1,
        "description": "test batch",
        "source_artifact": source.name,
        "source_artifact_sha256": sha256_file(source),
        "operations": operations,
        **extra,
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path


def test_batch_builds_a_verified_restore_folder(tmp_path, source):
    operations = [
        {"op": "clear_pattern", "pattern": 1},
        {
            "op": "set_cell",
            "pattern": 1,
            "step": 1,
            "sound": 3,
            "primary": "0e0981",
            "auxiliary": "f0",
        },
        {"op": "copy_pattern", "source": 1, "destination": 2},
        {"op": "set_footer", "pattern": 2, "footer": "6fffffffffffffff"},
        {"op": "clear_cell", "pattern": 2, "step": 1, "sound": 3, "note": "then restore it"},
        {
            "op": "set_cell",
            "pattern": 2,
            "step": 9,
            "sound": 3,
            "primary": "0e0981",
            "auxiliary": "f6",
        },
        {"op": "set_record_byte", "tag": "0x7d5c", "ordinal": 2, "offset": 129, "value": 100},
        {"op": "set_record_byte", "tag": 0x7D5C, "ordinal": 2, "offset": 131, "value": 7},
    ]
    spec = write_spec(tmp_path, source, operations, playback_seconds=12)
    out = tmp_path / "batch"
    report = build_batch(spec, out, base_dir=tmp_path)
    assert report["passed"] and report["no_op_operations"] == [8]
    assert sorted(p.name for p in out.iterdir()) == [
        "edited.symbols.npz",
        "experiment.json",
        "instructions.md",
        "redecoded.symbols.npz",
        "restore.wav",
        "software-validation.json",
        "spec.json",
    ]
    frame = decode_artifact(load_artifact(out / "edited.symbols.npz"))
    first, second = pattern_data(frame, 1), pattern_data(frame, 2)
    assert first == pattern_bytes([(1, 3, *NOTE)])
    assert second == pattern_bytes([(9, 3, "0e0981", 0xF6)], footer=b"\x6f" + b"\xff" * 7)
    assert frame.packets[2].payload[129] == 100
    experiment = json.loads((out / "experiment.json").read_text())
    assert experiment["expected_artifact"] == "edited.symbols.npz"
    assert experiment["playback_seconds"] == 12
    assert (out / experiment["source_artifact"]).resolve() == source.resolve()
    changes = report["expected_changes_from_source"]["changes"]
    assert {(c.get("pattern"), c["region"]) for c in changes} == {
        (1, "pattern_cell"),
        (2, "pattern_cell"),
        (2, "pattern_footer"),
        (None, "record"),
    }
    assert "Pattern 2 step 9 sound 3" in (out / "instructions.md").read_text()


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (
            {
                "op": "set_cell",
                "pattern": 1,
                "step": 1,
                "sound": 3,
                "primary": "0e09",
                "auxiliary": "f0",
            },
            "3 bytes",
        ),
        (
            {
                "op": "set_cell",
                "pattern": 17,
                "step": 1,
                "sound": 3,
                "primary": "0e0981",
                "auxiliary": "f0",
            },
            "pattern",
        ),
        (
            {
                "op": "set_cell",
                "pattern": 1,
                "step": 1,
                "sound": 3,
                "primary": "zz0981",
                "auxiliary": "f0",
            },
            "hex",
        ),
        ({"op": "set_footer", "pattern": 1}, "requires exactly"),
        ({"op": "copy_pattern", "source": 3, "destination": 3}, "different"),
        (
            {"op": "set_record_byte", "tag": "0x7d5c", "ordinal": 3, "offset": 1, "value": 1},
            "No packet #3",
        ),
        (
            {"op": "set_record_byte", "tag": "0x7d5c", "ordinal": 1, "offset": 200, "value": 1},
            "outside",
        ),
        ({"op": "rewrite_everything"}, "Unknown"),
    ],
)
def test_invalid_operations_are_rejected(source, operation, message):
    packets = decode_artifact(load_artifact(source)).packets
    with pytest.raises(ValueError, match=message):
        apply_operation(packets, operation)


def test_stale_source_hash_and_existing_output_are_rejected(tmp_path, source):
    spec = write_spec(tmp_path, source, [{"op": "clear_pattern", "pattern": 1}])
    data = json.loads(spec.read_text())
    data["source_artifact_sha256"] = "0" * 64
    spec.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="hash differs"):
        build_batch(spec, tmp_path / "out", base_dir=tmp_path)
    assert not (tmp_path / "out").exists()
    (tmp_path / "existing").mkdir()
    with pytest.raises(ValueError, match="fresh folder"):
        build_batch(spec, tmp_path / "existing", base_dir=tmp_path)


def test_unknown_spec_keys_are_rejected(tmp_path, source):
    spec = write_spec(tmp_path, source, [{"op": "clear_pattern", "pattern": 1}], surprise=1)
    with pytest.raises(ValueError, match="Unknown spec keys"):
        build_batch(spec, tmp_path / "out", base_dir=tmp_path)


def test_build_batch_cli(tmp_path, source, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    spec = write_spec(tmp_path, source, [{"op": "clear_pattern", "pattern": 1}])
    assert main(["build-batch", str(spec), "--out-dir", "cli-batch"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["passed"] and output["expected_change_count"] == 2
    assert (tmp_path / "cli-batch/restore.wav").exists()
    assert main(["build-batch", str(spec), "--out-dir", "cli-batch"]) == 2
