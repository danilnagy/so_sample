"""Fixed footer synthesis must preserve the opaque global and reject wider edits."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_pattern1_fx_up import reception_checks
from scripts.prepare_generated_pattern1_fx_up import (
    DIRECTORY,
    REGISTRATION,
    fixed_up_packets,
    footer_only_checks,
)


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments" / REGISTRATION
    if not path.exists():
        pytest.skip("Fixed generated FX-up registration required")
    registration = json.loads(path.read_text())
    folder = root / "experiments" / DIRECTORY
    source, target, recovered = [
        decode_artifact(load_artifact(item))
        for item in (
            root / registration["source_artifact"],
            folder / "edited.symbols.npz",
            folder / "redecoded.symbols.npz",
        )
    ]
    return root, folder, source, target, recovered, registration


@pytest.mark.capture
def test_actual_generated_waveform_entire_body_and_every_packet_roundtrip(states):
    root, folder, source, target, recovered, registration = states
    assert all(reception_checks(source, target, recovered, registration).values())
    assert target.encoded_body != source.encoded_body
    assert tuple(fixed_up_packets(source)) == target.packets
    validation_path = folder / "software-validation.json"
    validation = json.loads(validation_path.read_text())
    assert validation["passed"] and all(validation["checks"].values())
    assert not validation["hardware_verified"]
    for path, key in (
        (folder / "restore.wav", "restore_wav_sha256"),
        (folder / "edited.symbols.npz", "edited_artifact_sha256"),
        (validation_path, "software_validation_sha256"),
        (root / registration["source_artifact"], "source_artifact_sha256"),
    ):
        assert sha256_file(path) == registration[key]


@pytest.mark.capture
def test_earlier_genuine_up_body_with_global9_cannot_pass_global7_target(states):
    root, _, source, target, _, registration = states
    observed = json.loads((root / registration["earlier_recorded_up_observation"]).read_text())
    recorded = decode_artifact(load_artifact(root / observed["artifact_path"]))
    assert pattern_data(recorded, 1)[1024:] == pattern_data(target, 1)[1024:]
    assert recorded.packets[2].payload[131] == 9
    checks = reception_checks(source, target, recorded, registration)
    assert checks["all16_footer_nibbles_are6"] and checks["source_and_actual_native_valid"]
    assert not checks["global131_stays7"]
    assert not checks["only_eight_Pattern1_footer_bytes_changed"]
    assert not checks["entire_actual_body_and_packets_match_target"]


@pytest.mark.capture
@pytest.mark.parametrize("packet_index,offset", [(2, 130), (2, 131), (4, 1), (240, 15)])
def test_neighbor_global_note_sample_and_opaque_byte_changes_rejected(states, packet_index, offset):
    _, _, source, target, _, registration = states
    packets = list(target.packets)
    payload = bytearray(packets[packet_index].payload)
    payload[offset] ^= 1
    packets[packet_index] = Packet(packets[packet_index].tag, bytes(payload))
    actual = decode_frame(bytes(4095) + encode_packets(packets))
    checks = reception_checks(source, target, actual, registration)
    assert checks["source_and_actual_native_valid"]
    assert not checks["only_eight_Pattern1_footer_bytes_changed"]
    assert not checks["entire_actual_body_and_packets_match_target"]


@pytest.mark.capture
def test_clear_or_mixed_footer_is_not_accepted_as_uniform_up(states):
    _, _, source, target, _, registration = states
    checks = reception_checks(source, target, source, registration)
    assert not checks["all16_footer_nibbles_are6"]
    data = bytearray(pattern_data(target, 1))
    data[1024] = 0x67
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(target, 1, bytes(data)))
    )
    assert not footer_only_checks(source, actual)["all16_footer_nibbles_are6"]
    assert footer_only_checks(source, actual)["only_eight_Pattern1_footer_bytes_changed"]


@pytest.mark.capture
@pytest.mark.parametrize("value", [True, 6.0, "6", 7, 15])
def test_no_general_effect_value_constructor(states, value):
    _, _, source, _, _, _ = states
    with pytest.raises(ValueError, match="Only fixed research"):
        fixed_up_packets(source, value)


@pytest.mark.capture
def test_stale_source_and_target_pins_rejected(states):
    _, _, source, target, _, registration = states
    with pytest.raises(ValueError, match="Exact accepted"):
        fixed_up_packets(target)
    stale = copy.deepcopy(registration)
    stale["expected_body_sha256"] = hashlib.sha256(source.encoded_body).hexdigest()
    assert not reception_checks(source, target, target, stale)["target_body_matches_registration"]
