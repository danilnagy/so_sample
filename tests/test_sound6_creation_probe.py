"""Validate empty-slot creation against independent physical data and reject unsafe contexts."""

import hashlib
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
    sound_groups,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_drum_copy_control import excluding_destination_data
from scripts.check_sound4_growth_restore import comparison_checks as resize_checks
from scripts.check_sound6_creation_restore import comparison_checks
from scripts.make_sound6_creation_candidate import create_empty_owner_from_sound4_template


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def sources():
    root = Path(__file__).resolve().parents[1]
    shrink_folder = root / "experiments/edited-sound4-shrink-001"
    old_folder = root / "experiments/event-022-b-record-independent-sound4"
    if not (shrink_folder / "capture.wav").exists() or not (old_folder / "capture.wav").exists():
        pytest.skip("Genuine physical creation and generated shrink captures required")
    assert (
        sha256_file(shrink_folder / "capture.wav")
        == "4a11f64a99e10c2a6d49bcd3a1e4c4c5a2cc43ab481d1b884e396921b34fb3c5"
    )
    assert (
        sha256_file(old_folder / "capture.wav")
        == "06ba6534872d05e434485b031f458b1289d6acaa37dc59ac2482b3a8eb1c25a0"
    )
    shrink = decode_artifact(decode_wav(shrink_folder / "capture.wav", 0.0063))
    old_recorded = decode_artifact(decode_wav(old_folder / "capture.wav", 0.0063))
    old_base = decode_artifact(
        load_artifact(
            root
            / "experiments/event-021-b-drum10-step9-key2/derived/analysis-001/capture.symbols.npz"
        )
    )
    return root, shrink, old_base, old_recorded


@pytest.mark.capture
def test_actual_shrink_recapture_matches_target_and_preserves_every_other_record(sources):
    root, actual = sources[:2]
    folder = root / "experiments/edited-sound4-shrink-001"
    reg = json.loads((folder / "restore-registration.json").read_text())
    base = decode_artifact(load_artifact(root / reg["source_artifact"]))
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    assert all(resize_checks(base, target, actual, reg).values())
    assert actual.encoded_body == target.encoded_body and len(actual.packets) == 815


@pytest.mark.capture
def test_creation_reconstructs_entire_independent_empty_to_recorded_sound4_capture(sources):
    _, _, old_base, old_recorded = sources
    codes = np.frombuffer(sound_data(old_recorded, 3)[9:], dtype=np.uint8)
    result = create_empty_owner_from_sound4_template(old_base, old_recorded, 4, codes)
    assert encode_packets(result) == old_recorded.encoded_body


@pytest.mark.capture
def test_sound6_creation_is_self_owned_and_dropping_only_new_data_recovers_original(sources):
    base = sources[1]
    codes = np.arange(32768, dtype=np.uint32).astype(np.uint8)
    before = codes.copy()
    target = native(create_empty_owner_from_sound4_template(base, base, 6, codes))
    assert sound_data(target, 5) == bytes.fromhex("00000000c078000005") + codes.tobytes()
    assert len(target.packets) == 951 and target.end_byte == 190215
    assert excluding_destination_data(base, [5]) == excluding_destination_data(target, [5])
    assert encode_packets(excluding_destination_data(target, [5])) == base.encoded_body
    assert np.array_equal(codes, before)


@pytest.mark.capture
@pytest.mark.parametrize("slot", [True, 1, 5, 9, "6"])
def test_unknown_slots_and_bool_are_rejected(sources, slot):
    base = sources[1]
    with pytest.raises(ValueError):
        create_empty_owner_from_sound4_template(base, base, slot, np.zeros(32768, dtype=np.uint8))


@pytest.mark.capture
@pytest.mark.parametrize(
    "codes", [np.zeros(4096, dtype=np.uint8), np.zeros(32768), np.zeros((1, 32768), dtype=np.uint8)]
)
def test_wrong_code_count_type_and_shape_fail(sources, codes):
    base = sources[1]
    with pytest.raises(ValueError):
        create_empty_owner_from_sound4_template(base, base, 6, codes)


@pytest.mark.capture
def test_occupied_destination_and_dangling_reference_are_rejected(sources):
    base = sources[1]
    codes = np.zeros(32768, dtype=np.uint8)
    occupied = native(create_empty_owner_from_sound4_template(base, base, 6, codes))
    with pytest.raises(ValueError, match="no sample data"):
        create_empty_owner_from_sound4_template(occupied, occupied, 6, codes)
    index = sound_groups(base)[7][0]
    packets = list(base.packets)
    packets[index] = Packet(0xEF78, packets[index].payload[:8] + b"\x05")
    dangling = native(packets)
    with pytest.raises(ValueError, match="reference"):
        create_empty_owner_from_sound4_template(dangling, dangling, 6, codes)


@pytest.mark.capture
def test_unrelated_pattern_difference_and_excess_capacity_are_rejected(sources):
    root, base = sources[:2]
    codes = np.zeros(32768, dtype=np.uint8)
    pattern = bytearray(pattern_data(base, 1))
    pattern[905] = 16
    modified = native(_replace_pattern_data(base, 1, bytes(pattern)))
    with pytest.raises(ValueError, match="unrelated"):
        create_empty_owner_from_sound4_template(base, modified, 6, codes)
    large = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound4-growth-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    with pytest.raises(ValueError, match="capacity"):
        create_empty_owner_from_sound4_template(large, base, 6, codes)


@pytest.mark.capture
def test_recapture_checker_accepts_target_but_rejects_empty_baseline_and_changed_code(sources):
    base = sources[1]
    codes = np.zeros(32768, dtype=np.uint8)
    target = native(create_empty_owner_from_sound4_template(base, base, 6, codes))
    registration = {
        "source_body_sha256": hashlib.sha256(base.encoded_body).hexdigest(),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound6_header_hex": sound_data(target, 5)[:9].hex(),
        "expected_sound6_payload_sha256": hashlib.sha256(sound_data(target, 5)).hexdigest(),
        "expected_packet_count": 951,
        "expected_frame_end_byte": 190215,
    }
    assert all(comparison_checks(base, target, target, registration).values())
    stale = comparison_checks(base, target, base, registration)
    assert not stale["sound6_header_and_capacity_match"] and not stale["sound6_all_codes_match"]
    assert stale["all_non_sound6_plain_packets_preserved"]
    codes[123] = 5
    wrong = native(create_empty_owner_from_sound4_template(base, base, 6, codes))
    result = comparison_checks(base, target, wrong, registration)
    assert result["all_native_checksums"] and not result["sound6_all_codes_match"]
