"""Verify the genuine generated-copy recapture and bounded copied-slice previews."""

import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
)
from po33_re.formats.samples import decode_signed_mulaw, extract_calibrated_drum_slice_sound
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import export_project, packets_from_view
from scripts.validate_cross_drum_slice_recapture import comparison_checks


@pytest.fixture(scope="module")
def accepted_copy():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-drum-slice-copy-001"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine generated cross-drum copy recapture required")
    assert (
        sha256_file(capture) == "ac23213297cb3a1d0b56515bbb78bb5485b72cf5e420376ea591ae11f0d647cc"
    )
    registration = json.loads((directory / "restore-registration.json").read_text())
    original = decode_artifact(load_artifact(directory / registration["source_artifact"]))
    target = decode_artifact(load_artifact(directory / registration["generated_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return original, target, actual, registration, capture, artifact


@pytest.mark.capture
def test_genuine_recapture_matches_complete_target_and_all_registered_checks(accepted_copy):
    checks, packets, selectors, changes, values = comparison_checks(*accepted_copy[:4])
    assert all(checks.values()) and packets == [415] and selectors == [24]
    assert [c["offset"] for c in changes] == [0, 1, 4, 5]
    assert values["after"] == {"first_u32le": 4045, "second_u32le": 6045, "owner_id": 0}


@pytest.mark.capture
def test_copied_nonzero_preview_equals_exact_source_raw_window(accepted_copy):
    frame = accepted_copy[2]
    audio, report = extract_calibrated_drum_slice_sound(frame, 10, 1)
    source_audio, _ = extract_calibrated_drum_slice_sound(frame, 9, 2)
    raw = np.frombuffer(sound_data(frame, 0)[9:], dtype=np.uint8)
    assert np.array_equal(audio, source_audio)
    assert np.array_equal(audio, decode_signed_mulaw(raw[4045:6045]))
    assert len(audio) == report["preview_code_count"] == 2000
    assert report["selector_id"] == 24 and not report["pitch_and_gain_applied"]


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["unaccepted_end", "unaccepted_start", "owner", "neighbor"])
def test_copied_preview_rejects_unverified_window_and_neighbor_context(accepted_copy, damage):
    frame = accepted_copy[2]
    index = 417 if damage == "neighbor" else 415
    payload = bytearray(frame.packets[index].payload)
    if damage == "unaccepted_end":
        payload[4:8] = (6044).to_bytes(4, "little")
    elif damage == "unaccepted_start":
        payload[0] ^= 1
    elif damage == "owner":
        payload[8] = 1
    else:
        payload[4] ^= 1
    packets = list(frame.packets)
    packets[index] = Packet(frame.packets[index].tag, bytes(payload))
    altered = decode_frame(bytes(4095) + encode_packets(packets))
    with pytest.raises(ValueError):
        extract_calibrated_drum_slice_sound(altered, 10, 1)


@pytest.mark.capture
@pytest.mark.parametrize("slot,key", [(10, 2), (11, 1), (10, True), (10.0, 1)])
def test_copied_preview_does_not_broaden_other_key_or_slot_mapping(accepted_copy, slot, key):
    with pytest.raises(ValueError):
        extract_calibrated_drum_slice_sound(accepted_copy[2], slot, key)


@pytest.mark.capture
def test_export_copied_preview_reuses_source_audio_bytes_and_preserves_all_native_data(
    accepted_copy, tmp_path
):
    _, _, actual, _, capture, artifact = accepted_copy
    before = sha256_file(capture), sha256_file(artifact)
    output = tmp_path / "project"
    report = export_project(
        artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True
    )
    assert [(r["sound_slot"], r["slice_key"]) for r in report["preview_drum_slices"]] == [
        (9, 1),
        (9, 2),
        (10, 1),
    ]
    assert (output / "samples/10-slice-01.wav").read_bytes() == (
        output / "samples/09-slice-02.wav"
    ).read_bytes()
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert (
        sounds[9]["preview_slice_keys"] == [1]
        and sounds[9]["slice_records"][0]["export_frames"] == 4096
    )
    assert all(
        "keyboard_key" not in r and "preview_file" not in r for r in sounds[9]["slice_records"][1:]
    )
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
    assert (
        before == (sha256_file(capture), sha256_file(artifact)) and not report["hardware_verified"]
    )
    default = export_project(artifact, capture, tmp_path / "default")
    assert default["preview_drum_slices"] == []
