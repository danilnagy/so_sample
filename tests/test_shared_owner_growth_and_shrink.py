"""Verify real ownership transfer and keep unshared shrink/reuse predictions separate."""

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
    sound_groups,
)
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.formats.samples import sound_at_48k
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import export_project, packets_from_view
from scripts.check_shared_owner_rerecord import comparison_checks
from scripts.check_unshared_sound4_shrink import comparison_checks as shrink_checks


@pytest.fixture(scope="module")
def growth_capture():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/event-024-b-rerecord-shared-sound4"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine shared-owner re-recording required")
    assert (
        sha256_file(capture) == "5dca9a554b76bb538cf6a24deb5fdc707893730f6bea5519c76f5106342cb057"
    )
    registration = json.loads(
        (root / "experiments/shared-sound4-rerecord-predictions-001.json").read_text()
    )
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    shrink = json.loads(
        (root / "experiments/unshared-sound4-shrink-predictions-001.json").read_text()
    )
    return base, actual, registration, shrink, capture, artifact


def replace_sound4(frame, capacity, endpoint=16000, start=0):
    data = (
        start.to_bytes(4, "little") + endpoint.to_bytes(4, "little") + b"\x03" + b"\x55" * capacity
    )
    packets, current = [], None
    for packet in frame.packets:
        if packet.tag == 0x68B5:
            current = packet.payload[0]
            packets.append(packet)
            if current == 3:
                packets.extend(Packet(0xEF78, data[i : i + 255]) for i in range(0, len(data), 255))
        elif packet.tag != 0xEF78 or current != 3:
            packets.append(packet)
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_real_rerecord_transfers_entire_old_buffer_to_sound5_and_grows_source(growth_capture):
    checks, fits, changed, records, observed = comparison_checks(*growth_capture[:3])
    assert all(checks.values()) and changed == [3, 4]
    assert (
        fits["old_full_buffer_transferred_to_self_owned_sound5"]
        and fits["sound5_logical_sample_window_preserved"]
    )
    assert not fits["sound5_reference_unchanged_and_tracks_new_sound4"]
    assert records[0]["after"]["bytes_after_header"] == 73728
    assert observed["packet_count_delta"] == 305 and len(growth_capture[1].packets) == 985
    assert sound_data(growth_capture[0], 3)[9:] == sound_data(growth_capture[1], 4)[9:]


@pytest.mark.capture
def test_all_three_current_owned_buffers_match_actual4096_page_packet_order(growth_capture):
    actual = growth_capture[1]
    groups = sound_groups(actual)
    for selector in (0, 3, 4):
        code_count = len(sound_data(actual, selector)) - 9
        pages, remainder = divmod(code_count, 4096)
        assert remainder == 0
        lengths = [len(actual.packets[i].payload) for i in groups[selector]]
        assert lengths == [255] * 16 + [25] + ([255] * 16 + [16]) * (pages - 1)
    assert 73728 & (73728 - 1) != 0


@pytest.mark.capture
def test_new1250_and_retained1000_tones_fit_independently_and_old_audio_is_exact(growth_capture):
    base, actual = growth_capture[:2]
    old, _ = sound_at_48k(base, 4)
    new, _ = sound_at_48k(actual, 4)
    retained, _ = sound_at_48k(actual, 5)
    assert np.array_equal(old, retained)
    assert 1249 < measure_tone(new, 48000)["dominant_frequency_hz"] < 1251
    assert 999 < measure_tone(retained, 48000)["dominant_frequency_hz"] < 1001


@pytest.mark.capture
@pytest.mark.parametrize(
    "capacity,shrinks,reuses,multiple8192",
    [(20480, True, False, False), (32768, True, False, True), (73728, False, True, True)],
)
def test_capacity_shrink_and_reuse_are_independent_of_endpoint_reduction(
    growth_capture, capacity, shrinks, reuses, multiple8192
):
    base, registration = growth_capture[1], growth_capture[3]
    checks, fits, changed, _, observed = shrink_checks(
        base, replace_sound4(base, capacity), registration
    )
    assert all(checks.values()) and changed == [3]
    assert fits["new_sound4_endpoint_is_smaller"]
    assert fits["new_sound4_backing_capacity_shrinks"] is shrinks
    assert fits["new_sound4_backing_capacity_is_reused"] is reuses
    assert fits["new_backing_capacity_multiple4096"]
    assert fits["new_backing_capacity_multiple8192"] is multiple8192
    assert fits["sound5_full_buffer_and_header_preserved"]
    assert observed["sound4_after_window"]["backing_code_count"] == capacity


@pytest.mark.capture
def test_unknown_start_does_not_get_an_invented_resolved_window(growth_capture):
    base, registration = growth_capture[1], growth_capture[3]
    checks, fits, _, _, observed = shrink_checks(
        base, replace_sound4(base, 20480, start=1), registration
    )
    assert all(checks.values()) and not fits["new_sound4_window_is_zero_start_owner3"]
    assert not observed["sound4_after_window"]["resolved"]
    assert not fits["new_sound4_backing_capacity_shrinks"]


@pytest.mark.capture
def test_unchanged_state_or_pattern_changes_do_not_pass_shorter_recording_control(growth_capture):
    base, registration = growth_capture[1], growth_capture[3]
    checks, _, _, _, _ = shrink_checks(base, base, registration)
    assert not checks["sound4_record_changed"]
    smaller = replace_sound4(base, 20480)
    data = bytearray(pattern_data(smaller, 1))
    data[905] = 16
    altered = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(smaller, 1, bytes(data)))
    )
    checks, _, _, _, _ = shrink_checks(base, altered, registration)
    assert checks["all_native_checksums"] and not checks["all_patterns_unchanged"]


@pytest.mark.capture
def test_project_retains_three_independent_buffers_patterns_and_all_raw_tails(
    growth_capture, tmp_path
):
    _, actual, _, _, capture, artifact = growth_capture
    output = tmp_path / "project"
    report = export_project(
        artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True
    )
    assert report["preview_sound_slots"] == [1, 2, 3, 4, 5, 8]
    sounds = json.loads((output / "sounds.json").read_text())["sounds"]
    assert sounds[3]["backing_sound_id"] == 3 and sounds[3]["backing_bytes"] == 73728
    assert sounds[4]["backing_sound_id"] == 4 and sounds[4]["backing_bytes"] == 32768
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
    assert not report["hardware_verified"]
