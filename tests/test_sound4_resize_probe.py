"""Check observed shrink and a bounded template-based allocation reconstruction."""

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
from scripts.check_sound4_growth_restore import comparison_checks as restore_checks
from scripts.check_unshared_sound4_shrink import comparison_checks
from scripts.make_sound4_resize_candidate import resize_unshared_sound4_from_template


@pytest.fixture(scope="module")
def sources():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-025-b-rerecord-unshared-sound4-short"
    capture = folder / "capture.wav"
    if not capture.exists():
        pytest.skip("Genuine unshared shrink capture required")
    assert (
        sha256_file(capture) == "859e6eaeee774088e16eff03c60fedb909284de0ee2231c6c025d2aedfd7bf84"
    )
    actual = decode_artifact(decode_wav(capture, 0.0063))
    template = decode_artifact(
        load_artifact(
            root
            / "experiments/event-024-b-rerecord-shared-sound4/derived/analysis-001/capture.symbols.npz"
        )
    )
    return root, actual, template


def frame_from_packets(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.mark.capture
def test_real_short_recording_releases_capacity_and_preserves_other_state(sources):
    root, actual, template = sources
    reg = json.loads((root / "experiments/unshared-sound4-shrink-predictions-001.json").read_text())
    checks, fits, changed, _, observed = comparison_checks(template, actual, reg)
    assert all(checks.values()) and changed == [3]
    assert fits["new_sound4_backing_capacity_shrinks"]
    assert not fits["new_sound4_backing_capacity_is_reused"]
    assert fits["sound5_full_buffer_and_header_preserved"]
    assert observed["packet_count_delta"] == -170 and len(actual.packets) == 815
    assert observed["sound4_after_window"]["endpoint"] == 30912


@pytest.mark.capture
def test_resize_reproduces_entire_independently_recorded_larger_body(sources):
    _, actual, template = sources
    codes = np.frombuffer(sound_data(template, 3)[9:], dtype=np.uint8)
    original_codes = codes.copy()
    packets = resize_unshared_sound4_from_template(actual, template, codes)
    assert encode_packets(packets) == template.encoded_body
    assert np.array_equal(codes, original_codes)


@pytest.mark.capture
def test_new_codes_change_only_sound4_and_keep_all_opaque_packets(sources):
    _, actual, template = sources
    codes = np.arange(73728, dtype=np.uint32).astype(np.uint8)
    grown = frame_from_packets(resize_unshared_sound4_from_template(actual, template, codes))
    assert sound_data(grown, 3)[9:] == codes.tobytes()
    assert len(grown.packets) == 985 and grown.end_byte == 198568
    assert excluding_destination_data(actual, [3]) == excluding_destination_data(grown, [3])
    assert sound_data(actual, 4) == sound_data(grown, 4)


@pytest.mark.capture
@pytest.mark.parametrize("codes", [np.zeros(32768, dtype=np.uint8), np.zeros(73728), b"x"])
def test_unsupported_capacity_and_code_representation_fail(sources, codes):
    _, actual, template = sources
    with pytest.raises(ValueError):
        resize_unshared_sound4_from_template(actual, template, codes)


@pytest.mark.capture
def test_shared_owner_and_unrelated_template_changes_fail(sources):
    _, actual, template = sources
    codes = np.zeros(73728, dtype=np.uint8)
    index = sound_groups(actual)[4][0]
    packets = list(actual.packets)
    packets[index] = Packet(
        0xEF78, packets[index].payload[:8] + b"\x03" + packets[index].payload[9:]
    )
    with pytest.raises(ValueError, match="unshared"):
        resize_unshared_sound4_from_template(frame_from_packets(packets), template, codes)
    data = bytearray(pattern_data(template, 1))
    data[905] = 16
    modified = frame_from_packets(_replace_pattern_data(template, 1, bytes(data)))
    with pytest.raises(ValueError, match="unrelated"):
        resize_unshared_sound4_from_template(actual, modified, codes)


@pytest.mark.capture
def test_wrong_header_or_page_layout_fails(sources):
    _, actual, template = sources
    codes = np.zeros(73728, dtype=np.uint8)
    indices = sound_groups(actual)[3]
    packets = list(actual.packets)
    first = packets[indices[0]]
    packets[indices[0]] = Packet(first.tag, b"\x01" + first.payload[1:])
    with pytest.raises(ValueError, match="layout"):
        resize_unshared_sound4_from_template(frame_from_packets(packets), template, codes)
    packets = list(actual.packets)
    a, b = indices[15:17]
    packets[a], packets[b] = packets[b], packets[a]
    with pytest.raises(ValueError):
        resize_unshared_sound4_from_template(frame_from_packets(packets), template, codes)


@pytest.mark.capture
def test_growth_recapture_checker_rejects_stale_capture_and_corrupted_codes(sources):
    _, actual, template = sources
    codes = np.zeros(73728, dtype=np.uint8)
    target = frame_from_packets(resize_unshared_sound4_from_template(actual, template, codes))
    registration = {
        "source_body_sha256": hashlib.sha256(actual.encoded_body).hexdigest(),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound4_header_hex": sound_data(target, 3)[:9].hex(),
        "expected_sound4_payload_sha256": hashlib.sha256(sound_data(target, 3)).hexdigest(),
    }
    assert all(restore_checks(actual, target, target, registration).values())
    stale = restore_checks(actual, target, actual, registration)
    assert not stale["entire_recaptured_native_body_matches_target"]
    codes[123] = 7
    wrong = frame_from_packets(resize_unshared_sound4_from_template(actual, template, codes))
    checked = restore_checks(actual, target, wrong, registration)
    assert checked["all_native_checksums"] and checked["sound5_full_record_preserved"]
    assert not checked["sound4_all_codes_match"]


@pytest.fixture(scope="module")
def hardware_growth(sources):
    root = sources[0]
    folder = root / "experiments/edited-sound4-growth-001"
    if not (folder / "capture.wav").exists():
        pytest.skip("Generated growth hardware recapture required")
    assert (
        sha256_file(folder / "capture.wav")
        == "895d593e7a632fbd3154721a2c53b71b0dc69efffa627da8d5a62d9105c263f0"
    )
    actual = decode_artifact(decode_wav(folder / "capture.wav", 0.0063))
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    reg = json.loads((folder / "restore-registration.json").read_text())
    return actual, target, reg


@pytest.mark.capture
def test_real_generated_growth_recapture_is_exact_and_all_preservation_checks_pass(
    sources, hardware_growth
):
    actual, target, reg = hardware_growth
    assert actual.encoded_body == target.encoded_body
    assert all(restore_checks(sources[1], target, actual, reg).values())
    assert len(sound_data(actual, 3)) == 73737


@pytest.mark.capture
def test_inverse_resize_reconstructs_independent_short_capture_exactly(sources, hardware_growth):
    smaller = sources[1]
    larger = hardware_growth[0]
    codes = np.frombuffer(sound_data(smaller, 3)[9:], dtype=np.uint8)
    result = frame_from_packets(resize_unshared_sound4_from_template(larger, smaller, codes))
    assert result.encoded_body == smaller.encoded_body
    assert len(result.packets) == 815 and result.end_byte == 156758
    assert excluding_destination_data(larger, [3]) == excluding_destination_data(result, [3])


@pytest.mark.capture
def test_same_capacity_and_inverse_wrong_code_count_fail(sources, hardware_growth):
    smaller = sources[1]
    larger = hardware_growth[0]
    with pytest.raises(ValueError):
        resize_unshared_sound4_from_template(larger, larger, np.zeros(73728, dtype=np.uint8))
    with pytest.raises(ValueError):
        resize_unshared_sound4_from_template(larger, smaller, np.zeros(73728, dtype=np.uint8))


@pytest.mark.capture
def test_shrink_checker_rejects_unchanged_grown_state(sources, hardware_growth):
    smaller = sources[1]
    larger = hardware_growth[0]
    codes = np.zeros(32768, dtype=np.uint8)
    target = frame_from_packets(resize_unshared_sound4_from_template(larger, smaller, codes))
    registration = {
        "source_body_sha256": hashlib.sha256(larger.encoded_body).hexdigest(),
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
        "expected_sound4_header_hex": sound_data(target, 3)[:9].hex(),
        "expected_sound4_payload_sha256": hashlib.sha256(sound_data(target, 3)).hexdigest(),
        "expected_packet_count": 815,
        "expected_frame_end_byte": 156758,
    }
    assert all(restore_checks(larger, target, target, registration).values())
    stale = restore_checks(larger, target, larger, registration)
    assert not stale["expected_resize_geometry"] and not stale["sound4_all_codes_match"]
