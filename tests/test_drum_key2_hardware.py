"""Verify the clean key2 retry and both explicitly requested calibrated previews."""

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from scipy.signal import resample_poly

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.drums import replace_calibrated_drum_slice_end
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.samples import extract_calibrated_drum_slice_sound
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import packets_from_view
from scripts.validate_drum_key2_recapture import comparison_checks


@pytest.fixture(scope="module")
def key2_hardware():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-drum9-key2-end-001"
    capture = directory / "capture-retry.wav"
    artifact = directory / "derived/analysis-003/capture.symbols.npz"
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine clean nonzero-start drum recapture required")
    assert (
        sha256_file(capture) == "447b8e92224fd5db41f53bb283bff66317da14a32bf9b0004669aed057cfec91"
    )
    registration = json.loads((directory / "restore-registration.json").read_text())
    original, target = [
        decode_artifact(load_artifact(directory / registration[key]))
        for key in ("source_artifact", "generated_artifact")
    ]
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return original, target, actual, registration, capture, artifact


@pytest.mark.capture
def test_clean_key2_retry_matches_entire_target_and_preserves_accepted_key1(key2_hardware):
    checks, packets, selectors, changes, values = comparison_checks(*key2_hardware[:4])
    assert all(checks.values()) and packets == [385] and selectors == [9]
    assert changes == [{"offset": 4, "old": 76, "new": 157}, {"offset": 5, "old": 16, "new": 23}]
    assert values["after"] == {"first_u32le": 4045, "second_u32le": 6045, "owner_id": 0}


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["key2_endpoint", "key1_endpoint"])
def test_checksum_valid_wrong_endpoints_do_not_pass_whole_target_or_neighbor_checks(
    key2_hardware, damage
):
    original, target, actual, registration, _, _ = key2_hardware
    key, end = (2, 6046) if damage == "key2_endpoint" else (1, 2001)
    wrong = decode_frame(
        bytes(4095) + encode_packets(replace_calibrated_drum_slice_end(actual, 9, key, end))
    )
    checks, _, _, _, _ = comparison_checks(original, target, wrong, registration)
    assert checks["all_native_checksums"] and not checks["target_body_matches"]
    assert not checks["registered_body_hash_matches"]
    if damage == "key1_endpoint":
        assert (
            not checks["accepted_key1_preserved"]
            and not checks["exactly_one_sound9_reference_changed"]
        )


@pytest.mark.capture
def test_both_verified_slices_export_only_with_opt_in_and_match_unscaled_preview_policy(
    key2_hardware, tmp_path
):
    _, _, actual, _, capture, artifact = key2_hardware
    before = sha256_file(capture), sha256_file(artifact)
    args = ["export-project", str(artifact), "--capture", str(capture), "--calibrated-windows"]
    default = tmp_path / "default"
    assert main(args + ["--out-dir", str(default)]) == 0
    assert json.loads((default / "export-report.json").read_text())["preview_drum_slices"] == []
    enabled = tmp_path / "enabled"
    assert main(args + ["--calibrated-drum-slices", "--out-dir", str(enabled)]) == 0
    report = json.loads((enabled / "export-report.json").read_text())
    assert [r["slice_key"] for r in report["preview_drum_slices"]] == [1, 2]
    assert report["preview_sound_slots"] == [1, 2, 3, 8] and report["hardware_verified"] is False
    for key in (1, 2):
        path = enabled / f"samples/09-slice-{key:02}.wav"
        preview, rate = sf.read(path)
        expected, policy = extract_calibrated_drum_slice_sound(actual, 9, key)
        assert rate == 48000 and len(preview) == 4096 and sf.info(path).subtype == "FLOAT"
        assert np.allclose(preview, resample_poly(expected, 256, 125), atol=1e-7, rtol=0)
        assert policy["preview_code_count"] == 2000 and policy["pitch_and_gain_applied"] is False
    sound9 = json.loads((enabled / "sounds.json").read_text())["sounds"][8]
    assert sound9["preview_slice_keys"] == [1, 2]
    assert all("preview_file" not in record for record in sound9["slice_records"][2:])
    raw = json.loads((enabled / "source/packets.json").read_text())
    assert packets_from_view(raw) == actual.packets
    for name, record in report["files"].items():
        assert sha256_file(enabled / name) == record["sha256"]
    assert before == (sha256_file(capture), sha256_file(artifact))
