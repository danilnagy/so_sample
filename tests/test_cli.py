import json
import os

import pytest

from po33_re.cli import main


def test_compare_report_xor_and_safe_outputs(tmp_path, capsys):
    a, b = tmp_path / "a.bin", tmp_path / "b.bin"
    report, xor = tmp_path / "report.json", tmp_path / "xor.bin"
    a.write_bytes(bytes.fromhex("00 01 02 FF"))
    b.write_bytes(bytes.fromhex("00 03 02 FE 99"))
    args = ["compare", str(a), str(b), "--json", str(report), "--xor", str(xor)]
    assert main(args) == 0
    assert json.loads(report.read_text())["identical"] is False
    assert xor.read_bytes() == bytes.fromhex("00 02 00 01")
    assert main(args) == 2
    assert "Output exists" in capsys.readouterr().err
    assert main(args + ["--force"]) == 0
    original = a.read_bytes()
    assert main(["compare", str(a), str(b), "--json", str(a), "--force"]) == 2
    assert a.read_bytes() == original
    assert (
        main(["compare", str(a), str(b), "--json", str(report), "--xor", str(report), "--force"])
        == 2
    )


def test_missing_input_errors(tmp_path, capsys):
    assert main(["inspect", str(tmp_path / "missing.wav")]) == 2
    assert main(["encode", "missing", "--out", str(tmp_path / "fake.bin")]) == 2
    assert main(["roundtrip", "missing", "--out-dir", str(tmp_path / "missing-run")]) == 2
    assert not (tmp_path / "fake.bin").exists()
    assert "error:" in capsys.readouterr().err
    assert main([]) == 2


def test_stdout_json_and_tail(tmp_path, capsys):
    a, b = tmp_path / "a", tmp_path / "b"
    a.write_bytes(b"abc")
    b.write_bytes(b"abcd")
    assert main(["compare", str(a), str(b)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["tail_bytes"] == 1
    assert report["changed_ranges"] == []


@pytest.mark.parametrize("kind", ["hardlink", "symlink"])
def test_alias_rejected(tmp_path, kind):
    a, alias = tmp_path / "input", tmp_path / "alias"
    a.write_bytes(b"preserve me")
    try:
        if kind == "hardlink":
            os.link(a, alias)
        else:
            alias.symlink_to(a)
    except OSError as exc:
        pytest.skip(f"Filesystem cannot create {kind}: {exc}")
    assert main(["compare", str(a), str(a), "--json", str(alias), "--force"]) == 2
    assert a.read_bytes() == b"preserve me"


@pytest.mark.capture
def test_pattern_inspection_cli_writes_report_and_preserves_input(tmp_path):
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / (
        "experiments/edited-sample-001/derived/analysis-001/capture.symbols.npz"
    )
    if not source.exists():
        pytest.skip("Registered sample replacement recapture artifact required")
    before = source.read_bytes()
    report = tmp_path / "patterns.json"
    args = ["inspect-patterns", str(source), "--out", str(report)]
    assert main(args) == 0
    parsed = json.loads(report.read_text())
    assert (
        parsed["source_sha256"]
        == "94b9b95f3468f4781d52542756cb858479a2a4cd3969826ad31658479919312d"
    )
    assert len(parsed["patterns"]) == 16
    assert parsed["patterns"][0]["all_primary_and_auxiliary_bytes_zero"]
    assert main(args) == 2
    assert main(["inspect-patterns", str(source), "--out", str(source), "--force"]) == 2
    assert source.read_bytes() == before


@pytest.mark.capture
def test_clone_step_cli_produces_registered_body_and_preserves_input(tmp_path):
    from pathlib import Path

    from po33_re.formats.packets import decode_artifact
    from po33_re.modem.symbols import load_artifact

    source = Path(__file__).resolve().parents[1] / (
        "experiments/event-007-b-melodic/derived/analysis-001/capture.symbols.npz"
    )
    if not source.exists():
        pytest.skip("Registered melodic source artifact required")
    before = source.read_bytes()
    output, report = tmp_path / "cloned.npz", tmp_path / "clone.json"
    args = [
        "clone-step",
        str(source),
        "--pattern",
        "1",
        "--source-step",
        "1",
        "--target-steps",
        "5",
        "9",
        "13",
        "--out",
        str(output),
        "--report",
        str(report),
    ]
    assert main(args) == 0
    parsed = json.loads(report.read_text())
    assert parsed["native_frame"]["encoded_body_sha256"] == (
        "8b39765df9a4caf71e509f54b0c49e2f0d95ad1a60f4effa46daa687259d0104"
    )
    generated = load_artifact(output)
    assert generated.metadata["transformations"][-1]["kind"] == "opaque-step-clone"
    assert not generated.metadata["hardware_verified"]
    assert len(decode_artifact(generated).packets) == 511
    assert main(args) == 2
    assert (
        main(
            [
                "clone-step",
                str(source),
                "--pattern",
                "1",
                "--source-step",
                "1",
                "--target-steps",
                "5",
                "--out",
                str(source),
                "--force",
            ]
        )
        == 2
    )
    invalid_output = tmp_path / "invalid.npz"
    assert (
        main(
            [
                "clone-step",
                str(source),
                "--pattern",
                "1",
                "--source-step",
                "1",
                "--target-steps",
                "1",
                "--out",
                str(invalid_output),
            ]
        )
        == 2
    )
    assert not invalid_output.exists()
    assert source.read_bytes() == before


@pytest.mark.capture
def test_note_key_cli_preserves_source_and_rejects_unsupported_keys(tmp_path):
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / (
        "experiments/event-008-b-melodic-key2/derived/analysis-001/capture.symbols.npz"
    )
    if not source.exists():
        pytest.skip("Reviewed key2 source artifact required")
    before = source.read_bytes()
    output, report = tmp_path / "keys.npz", tmp_path / "keys.json"
    args = [
        "set-note-key",
        str(source),
        "--pattern",
        "1",
        "--step",
        "13",
        "--sound",
        "3",
        "--key",
        "2",
        "--out",
        str(output),
        "--report",
        str(report),
    ]
    assert main(args) == 0
    parsed = json.loads(report.read_text())
    assert parsed["kind"] == "calibrated-melodic-key-edit"
    assert parsed["native_frame"]["encoded_body_sha256"] == (
        "91b37d61e3bc71de72748dfd846892e62a7d839a9332f13a6f9c56687cdeadf0"
    )
    assert parsed["hardware_verified"] is False
    assert main(args) == 2
    assert (
        main(
            [
                "set-note-key",
                str(source),
                "--pattern",
                "1",
                "--step",
                "13",
                "--sound",
                "3",
                "--key",
                "2",
                "--out",
                str(source),
                "--force",
            ]
        )
        == 2
    )
    invalid = tmp_path / "unsupported.npz"
    assert (
        main(
            [
                "set-note-key",
                str(source),
                "--pattern",
                "1",
                "--step",
                "13",
                "--sound",
                "3",
                "--key",
                "3",
                "--out",
                str(invalid),
            ]
        )
        == 2
    )
    assert not invalid.exists()
    assert source.read_bytes() == before


@pytest.mark.capture
def test_clock_cli_recovers_recording_and_preserves_acquisition(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    capture = root / "experiments/edited-note-key-001/capture.wav"
    acquisition = root / "experiments/edited-note-key-001/derived/analysis-001/capture.symbols.npz"
    if not capture.exists() or not acquisition.exists():
        pytest.skip("Timing-slip recapture and original acquisition artifact required")
    before = acquisition.read_bytes()
    output, report = tmp_path / "clock.npz", tmp_path / "clock.json"
    args = [
        "decode-clock",
        str(capture),
        "--acquisition",
        str(acquisition),
        "--out",
        str(output),
        "--report",
        str(report),
    ]
    assert main(args) == 0
    parsed = json.loads(report.read_text())
    assert parsed["target_data_used"] is False
    assert (
        parsed["native_frame"]["encoded_body_sha256"]
        == "91b37d61e3bc71de72748dfd846892e62a7d839a9332f13a6f9c56687cdeadf0"
    )
    assert main(args) == 2
    assert (
        main(
            [
                "decode-clock",
                str(capture),
                "--acquisition",
                str(acquisition),
                "--out",
                str(acquisition),
                "--force",
            ]
        )
        == 2
    )
    wrong = root / "experiments/event-008-b-melodic-key2/derived/analysis-001/capture.symbols.npz"
    invalid = tmp_path / "invalid.npz"
    assert (
        main(["decode-clock", str(capture), "--acquisition", str(wrong), "--out", str(invalid)])
        == 2
    )
    assert not invalid.exists()
    assert acquisition.read_bytes() == before
