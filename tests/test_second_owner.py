"""Verify the genuine new allocation and independent second-owner copy predictions."""

import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.analysis.playback import measure_tone
from po33_re.artifacts import sha256_file
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
)
from po33_re.formats.samples import decode_signed_mulaw, extract_zero_start_sound, sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import export_project, packets_from_view
from scripts.check_sample_allocation_control import comparison_checks
from scripts.check_second_owner_copy_control import comparison_checks as copy_checks


@pytest.fixture(scope="module")
def second_owner():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-022-b-record-independent-sound4"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine second independent sample recording required")
    assert (
        sha256_file(capture) == "06ba6534872d05e434485b031f458b1289d6acaa37dc59ac2482b3a8eb1c25a0"
    )
    registration = json.loads(
        (root / "experiments/sound4-allocation-predictions-001.json").read_text()
    )
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    copy = json.loads((root / "experiments/sound4-to5-copy-predictions-001.json").read_text())
    return base, actual, registration, copy, capture, artifact


def with_sound5(frame, duplicate=False):
    data = sound_data(frame, 3)
    payload = data[:8] + b"\x04" + data[9:] if duplicate else data[:9]
    packets = list(frame.packets)
    index = next(i for i, packet in enumerate(packets) if packet == Packet(0x68B5, b"\x04"))
    chunks = [Packet(0xEF78, payload[i : i + 255]) for i in range(0, len(payload), 255)]
    packets[index + 1 : index + 1] = chunks
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_actual_allocation_all_saved_hypotheses_and_preservation_pass(second_owner):
    checks, fits, changed, _, observed = comparison_checks(*second_owner[:3])
    assert all(checks.values()) and all(fits.values()) and changed == [3]
    assert observed["sound4_raw_fields"] == {"first_u32le": 0, "second_u32le": 28608, "owner_id": 3}
    assert observed["sound4_payload_bytes"] == 32777 and observed["packet_count_delta"] == 136
    assert len(second_owner[1].packets) == 679 and second_owner[1].end_byte == 123301


@pytest.mark.capture
def test_new_owner_preview_decodes_only_declared_endpoint_and_retains_nonzero_tail(second_owner):
    frame = second_owner[1]
    data = sound_data(frame, 3)
    codes = np.frombuffer(data[9:], dtype=np.uint8)
    audio, report = extract_zero_start_sound(frame, 4)
    assert len(codes) == 32768 and len(audio) == 28608
    assert np.array_equal(audio, decode_signed_mulaw(codes[:28608]))
    assert report["backing_sound_id"] == 3 and np.count_nonzero(codes[28608:]) == 3974
    resampled, _ = sound_at_48k(frame, 4)
    fitted = measure_tone(resampled, 48000)
    assert 999 < fitted["dominant_frequency_hz"] < 1001
    assert fitted["single_sine_explained_variance"] > 0.99


@pytest.mark.capture
@pytest.mark.parametrize("duplicate", [False, True])
def test_reference_and_duplicate_buffer_hypotheses_are_independent_of_preservation(
    second_owner, duplicate
):
    actual, registration = second_owner[1], second_owner[3]
    checks, fits, changed, _ = copy_checks(actual, with_sound5(actual, duplicate), registration)
    assert all(checks.values()) and changed == [4]
    assert fits["destination_is_exact_owner3_reference"] is not duplicate
    assert fits["destination_is_duplicate_self_owned_buffer"] is duplicate
    assert fits["one_new_reference_packet_only"] is not duplicate


@pytest.mark.capture
@pytest.mark.parametrize("index,offset", [(111, 20), (377, 20), (4, 6)])
def test_source_buffer_other_owner_or_pattern_change_fails_copy_preservation(
    second_owner, index, offset
):
    actual, registration = second_owner[1], second_owner[3]
    packets = list(with_sound5(actual).packets)
    payload = bytearray(packets[index].payload)
    payload[offset] ^= 1
    packets[index] = Packet(packets[index].tag, bytes(payload))
    changed = decode_frame(bytes(4095) + encode_packets(packets))
    checks, _, _, _ = copy_checks(actual, changed, registration)
    assert checks["all_native_checksums"] and not all(checks.values())


@pytest.mark.capture
def test_project_preserves_two_buffers_patterns_and_raw_tail_with_new_sound4_preview(
    second_owner, tmp_path
):
    _, actual, _, _, capture, artifact = second_owner
    output = tmp_path / "project"
    report = export_project(
        artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True
    )
    assert report["preview_sound_slots"] == [1, 2, 3, 4, 8] and len(report["files"]) == 30
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert sounds[3]["backing_sound_id"] == 3 and sounds[3]["backing_bytes"] == 32768
    assert sounds[3]["export_frames"] == 58590
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
    assert not report["hardware_verified"]
