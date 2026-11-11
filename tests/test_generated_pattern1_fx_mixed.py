"""Mixed blocks preserve unrelated state and cannot silently become public per-step edits."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.effects import set_calibrated_pattern1_effect
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_pattern1_fx_mixed import reception_checks
from scripts.prepare_generated_pattern1_fx_mixed import DIRECTORY, REGISTRATION, fixed_mixed_packets


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments" / REGISTRATION
    if not path.exists():
        pytest.skip("Mixed-effect preregistration required")
    registration = json.loads(path.read_text())
    folder = root / "experiments" / DIRECTORY
    base, target, recovered = [
        decode_artifact(load_artifact(path))
        for path in (
            root / registration["source_artifact"],
            folder / "edited.symbols.npz",
            folder / "redecoded.symbols.npz",
        )
    ]
    return root, folder, base, target, recovered, registration


@pytest.mark.capture
def test_actual_waveform_native_exact_and_frozen_output_pins(states):
    _, folder, base, target, recovered, registration = states
    assert all(reception_checks(base, target, recovered, registration).values())
    assert tuple(fixed_mixed_packets(base)) == target.packets
    validation = json.loads((folder / "software-validation.json").read_text())
    assert validation["passed"] and all(validation["checks"].values())
    assert not validation["hardware_verified"]
    for name, key in (
        ("restore.wav", "restore_wav_sha256"),
        ("edited.symbols.npz", "edited_artifact_sha256"),
        ("software-validation.json", "software_validation_sha256"),
    ):
        assert sha256_file(folder / name) == registration[key]


@pytest.mark.capture
def test_both_nibble_orders_produce_same_halves_and_public_writer_stays_uniform_only(states):
    _, _, _, target, _, registration = states
    footer = pattern_data(target, 1)[1024:]
    for order in ((0, 4), (4, 0)):
        assert [(byte >> shift) & 15 for byte in footer for shift in order] == [6] * 8 + [7] * 8
    assert registration["low_nibble_first_values"] == registration["high_nibble_first_values"]
    with pytest.raises(ValueError, match="Mixed Pattern1"):
        set_calibrated_pattern1_effect(target, "none")


@pytest.mark.capture
@pytest.mark.parametrize("packet_index,offset", [(2, 131), (2, 130), (4, 6), (240, 15), (8, 4)])
def test_other_global_note_sample_and_footer_changes_fail_fixed_target(
    states, packet_index, offset
):
    _, _, base, target, _, registration = states
    packets = list(target.packets)
    payload = bytearray(packets[packet_index].payload)
    payload[offset] ^= 1
    packets[packet_index] = Packet(packets[packet_index].tag, bytes(payload))
    actual = decode_frame(bytes(4095) + encode_packets(packets))
    checks = reception_checks(base, target, actual, registration)
    assert checks["source_and_actual_native_valid"]
    assert not checks["entire_actual_body_and_packets_match_target"]
    if packet_index != 8:
        assert not checks["only_eight_Pattern1_footer_bytes_changed"]


@pytest.mark.capture
def test_unchanged_clear_and_stale_prediction_remain_failures(states):
    _, _, base, target, _, registration = states
    checks = reception_checks(base, target, base, registration)
    assert not checks["footer_is_fixed_6666666677777777"]
    assert not checks["entire_actual_body_and_packets_match_target"]
    stale = copy.deepcopy(registration)
    stale["expected_body_sha256"] = "0" * 64
    assert not reception_checks(base, target, target, stale)["target_body_matches_registration"]
    with pytest.raises(ValueError, match="Exact accepted clear"):
        fixed_mixed_packets(target)
