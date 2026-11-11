"""Keep the surprising trim result separate from successful preservation checks."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_sample_start_control import comparison_checks


@pytest.fixture(scope="module")
def genuine_start():
    root = Path(__file__).resolve().parents[1]
    base_path = (
        root / "experiments/edited-sound2-remove-001/derived/analysis-001/capture.symbols.npz"
    )
    capture = root / "experiments/event-012-b-sound3-start/capture.wav"
    if not base_path.exists() or not capture.exists():
        pytest.skip("Genuine removal baseline and nonzero-start control WAV required")
    assert (
        sha256_file(capture) == "24502f734e1d9170a1c5a4ac89d104fafeec3514478f39749919521336f68673"
    )
    base = decode_artifact(load_artifact(base_path))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    assert (
        hashlib.sha256(actual.encoded_body).hexdigest()
        == "4b697a34bea74f34654107463a9586afe31e9db1b55bf11f4f057f6e7f72ddc2"
    )
    registration = json.loads((root / "experiments/sound3-start-predictions-001.json").read_text())
    return base, actual, registration


def replace_packet(frame, index, payload):
    packets = list(frame.packets)
    packets[index] = Packet(packets[index].tag, payload)
    # Protocol-only counterexample: retain frame offsets without manufacturing a WAV.
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_genuine_start_control_preserves_all_other_state_and_rejects_both_second_field_hypotheses(
    genuine_start,
):
    checks, hypotheses, packets, changes, values = comparison_checks(*genuine_start)
    assert all(checks.values()) and packets == [375]
    assert [c["offset"] for c in changes] == [0, 1, 4, 5]
    assert hypotheses == {
        "first_field_is_start": True,
        "second_field_unchanged": False,
        "second_field_moves_with_start": False,
    }
    assert values["before"] == {"first_u32le": 0, "second_u32le": 8000, "owner_id": 0}
    assert values["after"] == {"first_u32le": 31393, "second_u32le": 65535, "owner_id": 0}


@pytest.mark.capture
@pytest.mark.parametrize("second,constant,moving", [(8000, True, False), (39393, False, True)])
def test_registered_alternatives_are_evaluated_separately_using_synthetic_vectors(
    genuine_start, second, constant, moving
):
    base, actual, registration = genuine_start
    payload = actual.packets[375].payload[:4] + second.to_bytes(4, "little") + b"\x00"
    vector = replace_packet(actual, 375, payload)
    checks, hypotheses, _, _, _ = comparison_checks(base, vector, registration)
    assert all(checks.values())
    assert hypotheses["second_field_unchanged"] is constant
    assert hypotheses["second_field_moves_with_start"] is moving


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["pattern", "owner_codes", "reference_owner"])
def test_valid_packet_checksums_do_not_hide_unrelated_changes(genuine_start, damage):
    base, actual, registration = genuine_start
    if damage == "pattern":
        index, offset = 4, 6
    elif damage == "owner_codes":
        index, offset = next(
            (i, 20) for i, p in enumerate(actual.packets) if p.tag == 0xEF78 and len(p.payload) > 9
        )
    else:
        index, offset = 375, 8
    payload = bytearray(actual.packets[index].payload)
    payload[offset] ^= 1
    changed = replace_packet(actual, index, bytes(payload))
    checks, _, _, _, _ = comparison_checks(base, changed, registration)
    assert checks["all_packet_checksums"] and checks["frame_end_byte"]
    assert not all(checks.values())
    assert not checks[
        {
            "pattern": "all_patterns_unchanged",
            "owner_codes": "backing_owner_unchanged",
            "reference_owner": "owner_id_unchanged",
        }[damage]
    ]
