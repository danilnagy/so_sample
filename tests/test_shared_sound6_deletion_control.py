"""Keep deletion transfer, retained backing and lost-copy outcomes distinguishable."""

import json
from pathlib import Path

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
from scripts.check_shared_sound6_deletion import comparison_checks, hypothetical_transfer_packets
from scripts.check_sound6_to7_copy_restore import comparison_checks as copy_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


def replace_record(frame, selector, data):
    packets, offset = list(frame.packets), 0
    for index in sound_groups(frame)[selector]:
        length = len(packets[index].payload)
        packets[index] = Packet(0xEF78, data[offset : offset + length])
        offset += length
    assert offset == len(data)
    return native(packets)


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound6-to7-copy-001"
    if not (folder / "capture.wav").exists():
        pytest.skip("Generated shared-reference hardware recapture required")
    assert (
        sha256_file(folder / "capture.wav")
        == "9737239d8d7b8f221eb23b0d7b8240f0a8799c3ad48482dc9e16ab94f4fc313f"
    )
    actual = decode_artifact(decode_wav(folder / "capture.wav", 0.0063))
    reg = json.loads((root / "experiments/shared-sound6-deletion-predictions-001.json").read_text())
    return root, actual, reg


@pytest.mark.capture
def test_real_copy_recapture_is_exact_and_owner5_has_only_sound6_and7(source):
    root, actual, _ = source
    folder = root / "experiments/edited-sound6-to7-copy-001"
    reg = json.loads((folder / "restore-registration.json").read_text())
    before = decode_artifact(load_artifact(root / reg["source_artifact"]))
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    assert all(copy_checks(before, target, actual, reg).values())
    assert sound_data(actual, 6) == sound_data(actual, 5)[:9]


@pytest.mark.capture
def test_hypothetical_full_transfer_passes_separately_from_retained_owner_alternative(source):
    _, base, reg = source
    after = native(hypothetical_transfer_packets(base))
    checks, fits, changed, _, observed = comparison_checks(base, after, reg)
    assert all(checks.values()) and changed == [5, 6]
    assert (
        fits["sound6_record_is_empty"]
        and fits["sound7_is_self_owned_full_buffer_with_all_codes_preserved"]
    )
    assert fits["sound7_logical_window_preserved"] and fits["full_transfer_entire_body_matches"]
    assert not fits["sound7_reference_still_points_to_old_owner5"]
    assert not fits["full_codes_remain_under_sound6_owner5"]
    assert observed["packet_count_delta"] == -1 and observed["native_body_byte_delta"] == -14


@pytest.mark.capture
def test_retaining_backing_with_zero_sound6_endpoint_is_not_misclassified_as_transfer(source):
    _, base, reg = source
    data = sound_data(base, 5)
    after = replace_record(base, 5, data[:4] + bytes(4) + data[8:])
    checks, fits, _, _, observed = comparison_checks(base, after, reg)
    assert all(checks.values())
    assert fits["sound7_logical_window_preserved"]
    assert (
        fits["sound7_reference_still_points_to_old_owner5"]
        and fits["full_codes_remain_under_sound6_owner5"]
    )
    assert not fits["sound6_record_is_empty"]
    assert not fits["sound7_is_self_owned_full_buffer_with_all_codes_preserved"]
    assert observed["sound7_after_window"]["owner_id"] == 5


@pytest.mark.capture
def test_lost_copy_is_a_reported_hypothesis_failure_not_repaired_or_assumed_preserved(source):
    _, base, reg = source
    after = native(excluding_destination_data(base, [5, 6]))
    checks, fits, _, _, observed = comparison_checks(base, after, reg)
    assert all(checks.values()) and fits["sound6_record_is_empty"]
    assert not fits["sound7_logical_window_preserved"]
    assert not fits["sound7_is_self_owned_full_buffer_with_all_codes_preserved"]
    assert not observed["sound7_after_window"]["resolved"]


@pytest.mark.capture
def test_tail_corruption_can_preserve_used_window_but_fails_complete_buffer_transfer(source):
    _, base, reg = source
    transferred = native(hypothetical_transfer_packets(base))
    data = bytearray(sound_data(transferred, 6))
    data[-1] = 7
    after = replace_record(transferred, 6, bytes(data))
    checks, fits, _, _, _ = comparison_checks(base, after, reg)
    assert all(checks.values()) and fits["sound7_logical_window_preserved"]
    assert not fits["sound7_is_self_owned_full_buffer_with_all_codes_preserved"]
    assert not fits["full_transfer_entire_body_matches"]


@pytest.mark.capture
def test_stale_baseline_or_pattern_change_fails_core_controls(source):
    _, base, reg = source
    checks, _, _, _, _ = comparison_checks(base, base, reg)
    assert not checks["state_changed_from_baseline"]
    transferred = native(hypothetical_transfer_packets(base))
    data = bytearray(pattern_data(transferred, 1))
    data[905] = 16
    wrong = native(_replace_pattern_data(transferred, 1, bytes(data)))
    checks, fits, _, _, _ = comparison_checks(base, wrong, reg)
    assert not checks["all_patterns_unchanged"] and fits["sound7_logical_window_preserved"]


@pytest.mark.capture
def test_unknown_sound7_start_does_not_get_a_guessed_logical_window(source):
    _, base, reg = source
    transferred = native(hypothetical_transfer_packets(base))
    data = sound_data(transferred, 6)
    after = replace_record(transferred, 6, b"\x01" + data[1:])
    checks, fits, _, _, observed = comparison_checks(base, after, reg)
    assert all(checks.values())
    assert not fits["sound7_logical_window_preserved"]
    assert not observed["sound7_after_window"]["resolved"]
