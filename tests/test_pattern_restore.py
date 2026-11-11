import json
from pathlib import Path

import pytest

from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.validate_pattern_recapture import comparison_checks


def candidate_frames():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "experiments/event-007-b-melodic/derived/analysis-001/capture.symbols.npz",
        root / "experiments/generated-pattern-four-001/edited.symbols.npz",
    ]
    if not all(p.exists() for p in paths):
        pytest.skip("Pinned source and generated candidate artifacts required for validator tests")
    original, generated = [decode_artifact(load_artifact(p)) for p in paths]
    registration = json.loads((root / "experiments/edited-pattern-001/experiment.json").read_text())
    return original, generated, registration


@pytest.mark.capture
def test_comparison_accepts_software_target_without_claiming_hardware_evidence():
    original, generated, registration = candidate_frames()
    # This exercises checks with software frames; no recapture or hardware report is created.
    checks, changes, steps = comparison_checks(original, generated, generated, registration)
    assert all(checks.values())
    assert changes == [4, 5, 6, 7]
    assert steps == [1, 5, 9, 13]


@pytest.mark.capture
def test_comparison_rejects_a_valid_but_unedited_backup():
    original, generated, registration = candidate_frames()
    checks, _, steps = comparison_checks(original, generated, original, registration)
    assert not all(checks.values())
    assert not checks["registered_body_sha256_matches"]
    assert not checks["expected_populated_steps"]
    assert checks["sample_packets_unchanged"]
    assert steps == [1]


@pytest.mark.capture
def test_comparison_rejects_sample_change_even_with_valid_crc_and_four_steps():
    original, generated, registration = candidate_frames()
    packets = list(generated.packets)
    index = next(i for i, p in enumerate(packets) if p.tag == 0xEF78 and len(p.payload) > 9)
    payload = bytearray(packets[index].payload)
    payload[9] ^= 1
    packets[index] = Packet(packets[index].tag, bytes(payload))
    actual = decode_frame(bytes(4095) + encode_packets(packets))
    checks, _, steps = comparison_checks(original, generated, actual, registration)
    assert checks["all_packet_checksums_valid"]
    assert checks["expected_populated_steps"]
    assert checks["expected_frame_end_byte"]
    assert not checks["registered_body_sha256_matches"]
    assert not checks["sample_packets_unchanged"]
    assert not checks["only_pattern_data_packets_changed"]
    assert steps == [1, 5, 9, 13]


@pytest.mark.capture
def test_genuine_after_playback_recapture_matches_registered_four_note_body():
    from po33_re.artifacts import sha256_file
    from po33_re.modem.decode import decode_wav

    original, generated, registration = candidate_frames()
    capture = Path(__file__).resolve().parents[1] / "experiments/edited-pattern-001/capture.wav"
    if not capture.is_file():
        pytest.skip("Genuine after-playback pattern recapture required")
    assert (
        sha256_file(capture) == "494957d160d0454eef3db5273e05496c59f98b6da89c0dc6bb25ee9115c182af"
    )
    actual = decode_artifact(decode_wav(capture, 0.0063))
    checks, changes, steps = comparison_checks(original, generated, actual, registration)
    assert all(checks.values())
    assert changes == [4, 5, 6, 7]
    assert steps == [1, 5, 9, 13]
    assert actual.encoded_body == generated.encoded_body
    assert actual.packets == generated.packets
