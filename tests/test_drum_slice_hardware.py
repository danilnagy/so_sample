"""Check exact drum-edit recapture and separately requested raw sample previews."""

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from scipy.signal import resample_poly

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.drums import replace_calibrated_drum_slice_end
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    rebuild_labels,
    sound_data,
    sound_groups,
)
from po33_re.formats.samples import decode_signed_mulaw, extract_calibrated_drum_slice_sound
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import packets_from_view
from scripts.validate_drum_slice_recapture import comparison_checks


@pytest.fixture(scope="module")
def drum_hardware():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-drum9-slice-end-001"
    capture = directory / "capture.wav"
    artifact = directory / "derived/analysis-001/capture.symbols.npz"
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine first generated drum-edit recapture required")
    assert (
        sha256_file(capture) == "0ddaf2dd97497f4046ccf69a346b03284e5701296a91686f6880a3cf88770c3e"
    )
    registration = json.loads((directory / "restore-registration.json").read_text())
    original, target = [
        decode_artifact(load_artifact(directory / registration[key]))
        for key in ("source_artifact", "generated_artifact")
    ]
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return original, target, actual, registration, capture, artifact


@pytest.mark.capture
def test_entire_registered_drum_hardware_body_matches(drum_hardware):
    checks, packets, changes, values = comparison_checks(*drum_hardware[:4])
    assert all(checks.values()) and packets == [383]
    assert changes == [{"offset": 4, "old": 127, "new": 208}, {"offset": 5, "old": 0, "new": 7}]
    assert values["after"] == {"first_u32le": 0, "second_u32le": 2000, "owner_id": 0}


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["endpoint", "neighbor"])
def test_valid_checksums_do_not_hide_wrong_target_or_neighbor_changes(drum_hardware, damage):
    original, target, actual, registration, _, _ = drum_hardware
    if damage == "endpoint":
        packets = replace_calibrated_drum_slice_end(actual, 9, 1, 2001)
    else:
        packets = list(actual.packets)
        index = sound_groups(actual)[9][0]
        payload = bytearray(packets[index].payload)
        payload[4] ^= 1
        packets[index] = Packet(0xEF78, bytes(payload))
    wrong = decode_frame(bytes(4095) + encode_packets(packets))
    checks, _, _, _ = comparison_checks(original, target, wrong, registration)
    assert checks["all_packet_checksums"] and not checks["target_body_matches"]
    assert not checks["registered_body_hash_matches"]
    if damage == "neighbor":
        assert not checks["only_reference_packet_changed"]


@pytest.mark.capture
def test_calibrated_drum_preview_reads_exact_unscaled_codes_and_rejects_other_keys(drum_hardware):
    frame = drum_hardware[2]
    audio, report = extract_calibrated_drum_slice_sound(frame, 9, 1)
    raw = np.frombuffer(sound_data(frame, 0)[9:], dtype=np.uint8)
    assert np.array_equal(audio, decode_signed_mulaw(raw[:2000]))
    assert len(audio) == report["preview_code_count"] == 2000
    assert report["pitch_and_gain_applied"] is False
    assert "inclusivity unresolved" in report["preview_selection_policy"]
    with pytest.raises(ValueError):
        extract_calibrated_drum_slice_sound(frame, 9, 3)


@pytest.mark.capture
def test_drum_export_requires_separate_opt_in_and_preserves_sources_and_all_raw_packets(
    drum_hardware, tmp_path
):
    _, _, actual, _, capture, artifact = drum_hardware
    before = sha256_file(capture), sha256_file(artifact)
    args = ["export-project", str(artifact), "--capture", str(capture), "--calibrated-windows"]
    default = tmp_path / "default"
    assert main(args + ["--out-dir", str(default)]) == 0
    report = json.loads((default / "export-report.json").read_text())
    assert report["preview_drum_slices"] == [] and not report["calibrated_drum_slices_requested"]
    assert not (default / "samples/09-slice-01.wav").exists()
    enabled = tmp_path / "enabled"
    assert main(args + ["--calibrated-drum-slices", "--out-dir", str(enabled)]) == 0
    report = json.loads((enabled / "export-report.json").read_text())
    assert report["preview_sound_slots"] == [1, 2, 3, 8]
    assert report["preview_drum_slices"] == [
        {"sound_slot": 9, "slice_key": 1, "file": "samples/09-slice-01.wav"},
        {"sound_slot": 9, "slice_key": 2, "file": "samples/09-slice-02.wav"},
    ]
    assert report["hardware_verified"] is False
    preview, rate = sf.read(enabled / "samples/09-slice-01.wav")
    expected, _ = extract_calibrated_drum_slice_sound(actual, 9, 1)
    assert rate == 48000 and len(preview) == 4096
    assert np.allclose(preview, resample_poly(expected, 256, 125), atol=1e-7, rtol=0)
    sounds = json.loads((enabled / "sounds.json").read_text())["sounds"]
    assert sounds[8]["preview_status"] == "exported_calibrated_drum_slices"
    assert sounds[8]["slice_records"][0]["preview_code_count"] == 2000
    assert all("preview_file" not in r for r in sounds[8]["slice_records"][2:])
    raw = json.loads((enabled / "source/packets.json").read_text())
    assert packets_from_view(raw) == actual.packets
    for name, record in report["files"].items():
        assert sha256_file(enabled / name) == record["sha256"]
    assert before == (sha256_file(capture), sha256_file(artifact))


@pytest.mark.capture
def test_unrecognized_slice_context_is_preserved_raw_without_a_drum_preview(
    drum_hardware, tmp_path
):
    _, _, actual, _, capture, artifact = drum_hardware
    packets = list(actual.packets)
    index = sound_groups(actual)[9][0]
    payload = bytearray(packets[index].payload)
    payload[4] ^= 1
    packets[index] = Packet(0xEF78, bytes(payload))
    edited = rebuild_labels(load_artifact(artifact), packets)
    modified = tmp_path / "modified.npz"
    modified.write_bytes(edited.to_bytes())
    output = tmp_path / "raw-context"
    assert (
        main(
            [
                "export-project",
                str(modified),
                "--capture",
                str(capture),
                "--calibrated-drum-slices",
                "--out-dir",
                str(output),
            ]
        )
        == 0
    )
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert "calibrated_drum_preview_reason" in sounds[8]
    assert not (output / "samples/09-slice-01.wav").exists()
    raw = json.loads((output / "source/packets.json").read_text())
    assert packets_from_view(raw) == tuple(packets)
