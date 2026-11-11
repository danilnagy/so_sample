"""Keep an odd serialized capacity distinct from rounding and unused-page removal."""

import json
from pathlib import Path

import numpy as np
import pytest

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
from po33_re.modem.symbols import load_artifact
from scripts.check_odd_page_sound6_restore import comparison_checks
from scripts.make_odd_page_sound6_candidate import create_nine_page_sound6


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound6-nine-pages-001"
    if not (folder / "edited.symbols.npz").exists():
        pytest.skip("Registered odd-page candidate required")
    reg = json.loads((folder / "restore-registration.json").read_text())
    base = decode_artifact(load_artifact(root / reg["source_artifact"]))
    template = decode_artifact(load_artifact(root / reg["template_artifact"]))
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    return base, template, target, reg


@pytest.mark.capture
def test_nine_page_candidate_only_adds_an_unused_zero_page_and_keeps_audio_exact(source):
    base, template, target, _ = source
    assert encode_packets(create_nine_page_sound6(base, template)) == target.encoded_body
    old, new = sound_data(template, 5), sound_data(target, 5)
    assert new == old + bytes(4096)
    assert len(new) - 9 == 36864 and (len(new) - 9) % 8192 != 0
    assert np.array_equal(sound_at_48k(template, 6)[0], sound_at_48k(target, 6)[0])


@pytest.mark.capture
def test_exact_nine_pages_and_truncated_eight_pages_are_classified_independently(source):
    base, template, target, reg = source
    checks, fits, _ = comparison_checks(base, target, target, reg)
    assert (
        all(checks.values())
        and fits["exact_nine_page_capacity36864"]
        and fits["entire_generated_native_body_matches"]
    )
    checks, fits, observed = comparison_checks(base, target, template, reg)
    assert all(checks.values()) and fits["unused_page_dropped_capacity32768"]
    assert (
        fits["original_header_and32768_code_prefix_preserved"] and fits["logical_window_preserved"]
    )
    assert not fits["entire_supplied36864_code_prefix_preserved"]
    assert observed["sound6_capacity_codes"] == 32768


@pytest.mark.capture
def test_rounding_to_ten_pages_does_not_get_reported_as_exact_restore(source):
    base, _, target, reg = source
    groups = sound_groups(target)
    last = groups[5][-1]
    packets = (
        target.packets[: last + 1]
        + (Packet(0xEF78, bytes(255)),) * 16
        + (Packet(0xEF78, bytes(16)),)
        + target.packets[last + 1 :]
    )
    checks, fits, observed = comparison_checks(base, target, native(packets), reg)
    assert all(checks.values()) and fits["rounded_ten_page_capacity40960"]
    assert fits["entire_supplied36864_code_prefix_preserved"] and fits["logical_window_preserved"]
    assert not fits["entire_generated_native_body_matches"]
    assert observed["sound6_capacity_codes"] == 40960


@pytest.mark.capture
def test_empty_baseline_and_changed_pattern_fail_core_controls(source):
    base, _, target, reg = source
    checks, _, _ = comparison_checks(base, target, base, reg)
    assert not checks["state_changed_from_baseline"] and not checks["sound6_record_present"]
    pattern = bytearray(pattern_data(target, 1))
    pattern[905] = 16
    checks, fits, _ = comparison_checks(
        base, target, native(_replace_pattern_data(target, 1, bytes(pattern))), reg
    )
    assert (
        not checks["all_patterns_unchanged"] and not fits["all_non_sound6_plain_packets_unchanged"]
    )


@pytest.mark.capture
def test_occupied_destination_and_unrelated_template_changes_fail(source):
    base, template, target, _ = source
    with pytest.raises(ValueError, match="empty"):
        create_nine_page_sound6(target, template)
    pattern = bytearray(pattern_data(template, 1))
    pattern[905] = 16
    with pytest.raises(ValueError, match="unrelated"):
        create_nine_page_sound6(base, native(_replace_pattern_data(template, 1, bytes(pattern))))
