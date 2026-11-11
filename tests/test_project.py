import copy
import json
import time
from pathlib import Path

import pytest
import soundfile as sf

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.packets import (
    END_TAG,
    START_TAG,
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
)
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from po33_re.project import packet_view, packets_from_view


def unknown_packet_frame():
    packets = (Packet(START_TAG, b""), Packet(0x1234, bytes(range(255))), Packet(END_TAG, b""))
    return decode_frame(encode_packets(packets), start=0)


def test_raw_packet_view_preserves_unknown_payloads_and_exact_native_body():
    frame = unknown_packet_frame()
    view = json.loads(json.dumps(packet_view(frame)))
    packets = packets_from_view(view)
    assert packets == frame.packets
    assert encode_packets(packets) == frame.encoded_body
    assert view["packets"][1] == {"tag": 0x1234, "payload_hex": bytes(range(255)).hex()}


@pytest.mark.parametrize("damage", ["schema", "count", "hash", "payload", "tag", "missing"])
def test_packet_view_rejects_malformed_or_inconsistent_data(damage):
    view = copy.deepcopy(packet_view(unknown_packet_frame()))
    if damage == "schema":
        view["schema_version"] = True
    elif damage == "count":
        view["packet_count"] += 1
    elif damage == "hash":
        view["encoded_body_sha256"] = "0" * 64
    elif damage == "payload":
        view["packets"][1]["payload_hex"] = "ff"
    elif damage == "tag":
        view["packets"][1]["tag"] = True
    else:
        del view["packets"][1]["payload_hex"]
    with pytest.raises(ValueError):
        packets_from_view(view)


@pytest.fixture
def genuine_source():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound2-remove-001"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine removal recapture and reviewed artifact required")
    assert (
        sha256_file(capture) == "aa8c083704bb92aa44893bafc3abd35e2bc05182fbb01ca7511f04752dafeb7d"
    )
    return capture, artifact


@pytest.mark.capture
def test_project_export_preserves_source_packets_patterns_and_shared_sample_previews(
    tmp_path, genuine_source, monkeypatch
):
    # Cross a timestamp boundary so alias previews cannot rely on fast encoding.
    original_write = sf.write

    def slow_write(*args, **kwargs):
        result = original_write(*args, **kwargs)
        time.sleep(1.1)
        return result

    monkeypatch.setattr(sf, "write", slow_write)
    capture, artifact = genuine_source
    unchanged = (sha256_file(capture), sha256_file(artifact))
    output = tmp_path / "project"
    args = ["export-project", str(artifact), "--capture", str(capture), "--out-dir", str(output)]
    assert main(args) == 0
    project = json.loads((output / "project.json").read_text())
    report = json.loads((output / "export-report.json").read_text())
    frame = decode_artifact(load_artifact(artifact))
    assert project["read_only"] is True and report["hardware_verified"] is False
    assert project["preview_sound_slots"] == [1, 2, 3, 8]
    assert all(report["checks"].values())
    assert (output / "source/capture.wav").read_bytes() == capture.read_bytes()
    assert (output / "source/capture.symbols.npz").read_bytes() == artifact.read_bytes()
    assert (output / "source/native-body.bin").read_bytes() == frame.encoded_body
    raw = json.loads((output / "source/packets.json").read_text())
    assert packets_from_view(raw) == frame.packets
    for entry in project["patterns"]:
        view = json.loads((output / entry["file"]).read_text())
        assert bytes.fromhex(view["data_hex"]) == pattern_data(frame, entry["pattern_slot"])
    pattern1 = json.loads((output / "patterns/01.json").read_text())
    assert [
        (e["step"], e["candidate_sound_slot"], e["calibrated_keyboard_key"])
        for e in pattern1["observed_cells"]
    ] == [(1, 3, 1), (5, 3, 2), (9, 2, 1), (9, 3, 7), (13, 3, 16)]
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert [
        s["sound_slot"] for s in sounds if s["preview_status"] == "exported_zero_start_melodic"
    ] == [1, 2, 3, 8]
    assert all(sounds[slot - 1]["backing_sound_id"] == 0 for slot in [1, 2, 3, 8])
    assert (
        (output / "samples/01.wav").read_bytes()
        == (output / "samples/02.wav").read_bytes()
        == (output / "samples/08.wav").read_bytes()
    )
    info = sf.info(output / "samples/03.wav")
    assert (
        info.samplerate == 48000
        and info.channels == 1
        and info.frames == 16384
        and info.subtype == "FLOAT"
    )
    for name, entry in report["files"].items():
        assert sha256_file(output / name) == entry["sha256"]
        assert (output / name).stat().st_size == entry["bytes"]
    before_report = (output / "export-report.json").read_bytes()
    assert main(args) == 2
    assert (output / "export-report.json").read_bytes() == before_report
    assert unchanged == (sha256_file(capture), sha256_file(artifact))


@pytest.mark.capture
def test_project_export_rejects_wrong_capture_and_input_aliases_before_creating_output(
    tmp_path, genuine_source
):
    capture, artifact = genuine_source
    wrong = tmp_path / "wrong.wav"
    wrong.write_bytes(capture.read_bytes() + b"changed")
    output = tmp_path / "invalid-project"
    assert (
        main(["export-project", str(artifact), "--capture", str(wrong), "--out-dir", str(output)])
        == 2
    )
    assert not output.exists()
    unchanged = artifact.read_bytes()
    assert (
        main(
            ["export-project", str(artifact), "--capture", str(capture), "--out-dir", str(artifact)]
        )
        == 2
    )
    assert artifact.read_bytes() == unchanged


@pytest.mark.capture
def test_nonzero_start_is_preserved_raw_without_an_invented_sample_preview(tmp_path):
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-012-b-sound3-start"
    artifact = directory / "derived/analysis-001/capture.symbols.npz"
    capture = directory / "capture.wav"
    if not artifact.exists() or not capture.exists():
        pytest.skip("Genuine nonzero-start control and reviewed artifact required")
    output = tmp_path / "nonzero-project"
    assert (
        main(["export-project", str(artifact), "--capture", str(capture), "--out-dir", str(output)])
        == 0
    )
    project = json.loads((output / "project.json").read_text())
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert project["preview_sound_slots"] == [1, 2, 8]
    assert sounds[2]["preview_status"] == "unsupported_layout_preserved_raw"
    assert not (output / "samples/03.wav").exists()
    frame = decode_artifact(load_artifact(artifact))
    raw = json.loads((output / "source/packets.json").read_text())
    assert packets_from_view(raw) == frame.packets
    assert raw["packets"][375]["payload_hex"] == "a17a0000ffff000000"


@pytest.mark.capture
def test_opt_in_verified_window_preview_retains_exact_packets_and_selection_policy(tmp_path):
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-nonzero-trim-001"
    artifact, capture = (
        directory / "derived/analysis-001/capture.symbols.npz",
        directory / "capture.wav",
    )
    if not artifact.exists() or not capture.exists():
        pytest.skip("Genuine verified window recapture required")
    output = tmp_path / "window-project"
    assert (
        main(
            [
                "export-project",
                str(artifact),
                "--capture",
                str(capture),
                "--out-dir",
                str(output),
                "--calibrated-windows",
            ]
        )
        == 0
    )
    project = json.loads((output / "project.json").read_text())
    sound = json.loads((output / "sounds.json").read_text())["sounds"][2]
    assert project["preview_sound_slots"] == [1, 2, 3, 8]
    assert project["calibrated_windows_requested"] is True
    assert sound["preview_status"] == "exported_calibrated_fixed_start_window"
    assert sound["start_field"] == 31393 and sound["endpoint_field"] == 39393
    assert "inclusivity unresolved" in sound["preview_selection_policy"]
    assert sf.info(output / "samples/03.wav").frames == 16384
    raw = json.loads((output / "source/packets.json").read_text())
    assert packets_from_view(raw) == decode_artifact(load_artifact(artifact)).packets
