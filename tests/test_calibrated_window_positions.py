"""Verify two-start window editing against independent hardware captures and guard limits."""

import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.edits import apply_plan
from po33_re.formats.packets import (
    decode_artifact,
    decode_frame,
    encode_packets,
    replace_calibrated_reference_end,
    replace_calibrated_reference_window,
    sound_data,
)
from po33_re.formats.samples import decode_signed_mulaw, extract_calibrated_window_sound
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.validate_nonzero_trim_recapture import comparison_checks


@pytest.fixture(scope="module")
def verified_positions():
    root = Path(__file__).resolve().parents[1]
    old_path = root / "experiments/edited-nonzero-trim-001/derived/analysis-001/capture.symbols.npz"
    new_path = (
        root / "experiments/edited-quarter-window-001/derived/analysis-003/capture.symbols.npz"
    )
    capture = root / "experiments/edited-quarter-window-001/capture-retry.wav"
    if not all(p.exists() for p in (old_path, new_path, capture)):
        pytest.skip("Both independently verified window captures required")
    assert (
        sha256_file(capture) == "fa3c5f47983a46b1ce1a7f533eff7df94f6cdefed13efe7bafa6b5f190ff86cb"
    )
    new = decode_artifact(decode_wav(capture, 0.0063))
    old = decode_artifact(load_artifact(old_path))
    assert new.encoded_body == decode_artifact(load_artifact(new_path)).encoded_body
    return old_path, new_path, old, new


@pytest.mark.capture
def test_window_repositioning_reproduces_both_entire_independent_hardware_bodies(
    verified_positions,
):
    _, _, old, new = verified_positions
    assert (
        encode_packets(replace_calibrated_reference_window(old, 3, 11716, 19716))
        == new.encoded_body
    )
    assert (
        encode_packets(replace_calibrated_reference_window(new, 3, 31393, 39393))
        == old.encoded_body
    )


@pytest.mark.capture
@pytest.mark.parametrize(
    "start,end",
    [
        (11715, 19716),
        (20000, 28000),
        (11716, 11826),
        (11716, 19717),
        (31393, 31503),
        (31393, 65536),
        (True, 19716),
        (11716.0, 19716),
        (11716, True),
    ],
)
def test_repositioning_rejects_interpolated_starts_and_crossed_local_bounds(
    verified_positions, start, end
):
    new = verified_positions[3]
    unchanged = new.encoded_body
    with pytest.raises(ValueError):
        replace_calibrated_reference_window(new, 3, start, end)
    assert new.encoded_body == unchanged


@pytest.mark.capture
def test_new_start_preview_matches_exact_unscaled_backing_slice(verified_positions):
    new = verified_positions[3]
    audio, report = extract_calibrated_window_sound(new, 3)
    raw = np.frombuffer(sound_data(new, 0)[9:], dtype=np.uint8)
    assert np.array_equal(audio, decode_signed_mulaw(raw[11716:19716]))
    assert report["start_field"] == 11716 and len(audio) == report["preview_code_count"] == 8000
    with pytest.raises(ValueError):
        replace_calibrated_reference_end(new, 3, 31504)


@pytest.mark.capture
def test_second_window_hardware_checks_reject_checksum_valid_wrong_endpoint(verified_positions):
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-quarter-window-001"
    registration = json.loads((directory / "restore-registration.json").read_text())
    original = decode_artifact(load_artifact(directory / registration["source_artifact"]))
    target = decode_artifact(load_artifact(directory / registration["generated_artifact"]))
    actual = verified_positions[3]
    checks, _, _, _ = comparison_checks(original, target, actual, registration)
    assert all(checks.values())
    wrong = decode_frame(
        bytes(4095) + encode_packets(replace_calibrated_reference_end(actual, 3, 19715))
    )
    checks, _, _, _ = comparison_checks(original, target, wrong, registration)
    assert checks["all_packet_checksums"] and not checks["endpoint_field_matches"]
    assert not checks["target_body_matches"]


@pytest.mark.capture
def test_window_plan_and_cli_reproduce_hardware_body_with_correct_start_provenance(
    verified_positions, tmp_path
):
    old_path, _, _, new = verified_positions
    source = load_artifact(old_path)
    unchanged = source.to_bytes()
    plan = {
        "schema": "po33.edit-plan",
        "schema_version": 1,
        "source_artifact_sha256": sha256_file(old_path),
        "source_body_sha256": "b3296f2ed7b3a74cedc79b8d89900e5128c7da1da0e2fed9839d1858412eddfe",
        "operations": [{"operation": "set_sound_window", "sound": 3, "start": 11716, "end": 19716}],
    }
    edited, trace = apply_plan(source, sha256_file(old_path), plan)
    assert decode_artifact(edited).encoded_body == new.encoded_body
    assert source.to_bytes() == unchanged and len(trace) == 1
    output, report = tmp_path / "window.npz", tmp_path / "window.json"
    assert (
        main(
            [
                "set-sound-window",
                str(old_path),
                "--sound",
                "3",
                "--start",
                "11716",
                "--end",
                "19716",
                "--out",
                str(output),
                "--report",
                str(report),
            ]
        )
        == 0
    )
    assert decode_artifact(load_artifact(output)).encoded_body == new.encoded_body
    metadata = json.loads(report.read_text())
    assert metadata["start_field"] == 11716 and metadata["hardware_verified"] is False
    second = tmp_path / "endpoint.npz"
    second_report = tmp_path / "endpoint.json"
    assert (
        main(
            [
                "set-sound-end",
                str(output),
                "--sound",
                "3",
                "--end",
                "11827",
                "--out",
                str(second),
                "--report",
                str(second_report),
            ]
        )
        == 0
    )
    assert json.loads(second_report.read_text())["start_field"] == 11716
    assert source.to_bytes() == unchanged
