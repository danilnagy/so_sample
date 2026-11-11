"""Ordinary playback must not hide footer, note, sample or neighboring global changes."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.modem.symbols import load_artifact
from scripts.check_pattern1_playback_global_control import (
    playback_report,
    require_independent_captures,
)


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/pattern1-playback-global-registration-001.json"
    if not path.exists():
        pytest.skip("Accepted clear and playback registration required")
    registration = json.loads(path.read_text())
    return decode_artifact(load_artifact(root / registration["source_artifact"])), registration


def changed(frame, packet_index, offset, value):
    packets = list(frame.packets)
    payload = bytearray(packets[packet_index].payload)
    payload[offset] = value
    packets[packet_index] = Packet(packets[packet_index].tag, bytes(payload))
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
@pytest.mark.parametrize("value", [7, 9, 128])
def test_unchanged_state_and_low4_vs_whole_byte_are_distinct(source, value):
    base, registration = source
    actual = changed(base, 2, 131, value)
    report = playback_report(base, base, actual, registration)
    assert report["source_body_matches_registration"]
    assert report["all_native_controls_pass"]
    assert report["stopped_repeat_entire_body_equal_source_prediction"]
    assert all(report["both_footers_remain_no_FX"])
    assert report["plain_playback_whole_byte_scope_against_repeat"]
    assert report["plain_playback_low4_scope_against_repeat"] is (value < 16)
    assert report["plain_playback_global_changed_from_repeat_diagnostic"] is (value != 7)


@pytest.mark.capture
@pytest.mark.parametrize("packet_index,offset", [(2, 130), (8, 4), (4, 1), (240, 15)])
def test_other_global_footer_note_and_sample_changes_cannot_hide(source, packet_index, offset):
    base, registration = source
    actual = changed(base, packet_index, offset, base.packets[packet_index].payload[offset] ^ 1)
    report = playback_report(base, base, actual, registration)
    assert report["all_native_controls_pass"]
    assert not report["plain_playback_low4_scope_against_repeat"]
    assert not report["plain_playback_whole_byte_scope_against_repeat"]


@pytest.mark.capture
def test_repeat_failure_and_stale_source_remain_failures(source):
    base, registration = source
    repeated = changed(base, 2, 131, 9)
    report = playback_report(base, repeated, repeated, registration)
    assert not report["stopped_repeat_entire_body_equal_source_prediction"]
    assert report["plain_playback_low4_scope_against_repeat"]
    stale = copy.deepcopy(registration)
    stale["source_body_sha256"] = "0" * 64
    assert not playback_report(base, base, base, stale)["source_body_matches_registration"]
    stale = copy.deepcopy(registration)
    stale["global_candidate"]["payload_offset"] = 130
    with pytest.raises(ValueError, match="fixed registered"):
        playback_report(base, base, base, stale)


@pytest.mark.parametrize("hashes", [("a", "b"), ("b", "b")])
def test_duplicate_raw_capture_rejected(hashes):
    with pytest.raises(ValueError, match="Independent NEW raw WAVs"):
        require_independent_captures("a", hashes)


def test_independent_raw_identity_allows_identical_native_state():
    require_independent_captures("a", ["b", "c"])
