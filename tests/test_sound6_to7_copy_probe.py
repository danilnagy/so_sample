"""Validate generated melodic reference copying against an independent physical copy."""

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
from po33_re.formats.samples import sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_sound6_creation_restore import comparison_checks as creation_checks
from scripts.check_sound6_to7_copy_restore import comparison_checks
from scripts.make_sound6_to7_copy_candidate import copy_owned_reference_to_empty_slot


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound6-create-001"
    if not (folder / "capture.wav").exists():
        pytest.skip("Generated Sound6 creation hardware recapture required")
    assert (
        sha256_file(folder / "capture.wav")
        == "e21b04a85d73f1f53cb4cbefb1926c17c7f42ab4272c6cce09037a307a8cc776"
    )
    frame = decode_artifact(decode_wav(folder / "capture.wav", 0.0063))
    return root, frame


@pytest.mark.capture
def test_real_sound6_creation_matches_target_with_every_unrelated_packet_preserved(source):
    root, actual = source
    folder = root / "experiments/edited-sound6-create-001"
    reg = json.loads((folder / "restore-registration.json").read_text())
    base = decode_artifact(load_artifact(root / reg["source_artifact"]))
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    assert all(creation_checks(base, target, actual, reg).values())
    assert actual.encoded_body == target.encoded_body and len(actual.packets) == 951


@pytest.mark.capture
def test_builder_reproduces_independent_physical_sound4_to5_copy(source):
    root = source[0]
    before = decode_artifact(
        load_artifact(
            root
            / "experiments/event-022-b-record-independent-sound4/derived/analysis-001/capture.symbols.npz"
        )
    )
    folder = root / "experiments/event-023-b-copy-sound4-to-sound5"
    # Independently decode the original physical waveform at its reviewed fixed profile.
    copied = decode_artifact(decode_wav(folder / "capture.wav", 0.004))
    assert encode_packets(copy_owned_reference_to_empty_slot(before, 4, 5)) == copied.encoded_body


@pytest.mark.capture
def test_reference_copy_shares_same_preview_without_duplicating_codes(source):
    base = source[1]
    copied = native(copy_owned_reference_to_empty_slot(base, 6, 7))
    assert sound_data(copied, 6) == bytes.fromhex("00000000c078000005")
    assert sound_data(copied, 5) == sound_data(base, 5)
    assert np.array_equal(sound_at_48k(copied, 6)[0], sound_at_48k(copied, 7)[0])
    assert len(copied.packets) == 952 and copied.end_byte == 190229
    assert len(copied.encoded_body) - len(base.encoded_body) == 14


@pytest.mark.capture
@pytest.mark.parametrize("pair", [(True, 7), (6, True), (6, 6), (7, 6), (6, 8)])
def test_unknown_pairs_and_bools_fail(source, pair):
    with pytest.raises(ValueError):
        copy_owned_reference_to_empty_slot(source[1], *pair)


@pytest.mark.capture
def test_occupied_destination_wrong_header_and_existing_sharing_fail(source):
    base = source[1]
    copied = native(copy_owned_reference_to_empty_slot(base, 6, 7))
    with pytest.raises(ValueError, match="empty"):
        copy_owned_reference_to_empty_slot(copied, 6, 7)
    index = sound_groups(base)[5][0]
    packets = list(base.packets)
    original = packets[index].payload
    packets[index] = Packet(0xEF78, b"\x01" + original[1:])
    with pytest.raises(ValueError, match="layout"):
        copy_owned_reference_to_empty_slot(native(packets), 6, 7)
    packets = list(base.packets)
    index = sound_groups(base)[7][0]
    packets[index] = Packet(0xEF78, sound_data(base, 5)[:9])
    with pytest.raises(ValueError, match="unshared"):
        copy_owned_reference_to_empty_slot(native(packets), 6, 7)


@pytest.mark.capture
def test_checker_rejects_empty_baseline_and_wrong_reference_owner(source):
    base = source[1]
    target = native(copy_owned_reference_to_empty_slot(base, 6, 7))
    registration = {
        "source_body_sha256": hashlib.sha256(base.encoded_body).hexdigest(),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound7_reference_hex": sound_data(target, 6).hex(),
        "expected_sound6_payload_sha256": hashlib.sha256(sound_data(target, 5)).hexdigest(),
        "expected_packet_count": 952,
        "expected_frame_end_byte": 190229,
    }
    assert all(comparison_checks(base, target, target, registration).values())
    stale = comparison_checks(base, target, base, registration)
    assert not stale["sound7_exact_reference"] and stale["sound6_full_buffer_preserved"]
    index = sound_groups(target)[6][0]
    packets = list(target.packets)
    packets[index] = Packet(0xEF78, packets[index].payload[:8] + b"\x03")
    wrong = comparison_checks(base, target, native(packets), registration)
    assert wrong["all_native_checksums"] and not wrong["sound7_exact_reference"]
    assert not wrong["owner5_has_only_sound6_and7_referrers"]
