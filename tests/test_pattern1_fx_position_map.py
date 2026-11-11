import numpy as np
import pytest
import soundfile as sf
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from scripts.pattern1_fx_multi_step_pitch_method import decide, note_tracks, step_results
from scripts.prepare_pattern1_fx_position_map import (
    FOOTER,
    PREDICTIONS,
    position_map_checks,
    position_map_pattern,
)

RATE = 44100
REFERENCE = 1190.417
SINGLE_TONE = pattern_bytes([(1, 3, "0e0981", 0xF0)])


def note(rise):
    t = np.arange(round(0.21 * RATE)) / RATE
    ratio = 1 + rise * np.minimum(t, 0.15) / 0.15
    return 0.3 * np.sin(2 * np.pi * np.cumsum(REFERENCE * ratio) / RATE)


def write_loops(path, rises, loops=6):
    """rises maps step -> pitch rise within that step's note."""
    step = round(0.15 * RATE)
    loop = np.zeros(16 * step)
    for s, rise in rises.items():
        tone = note(rise)
        start = (s - 1) * step
        loop[start : start + len(tone)] += tone
    mono = np.r_[np.zeros(RATE), np.tile(loop, loops)]
    sf.write(path, np.column_stack((mono, mono)), RATE, subtype="PCM_16")


def frame_of(packets):
    return decode_frame(encode_packets(packets), start=0)


def test_pattern_places_four_identical_notes_and_the_footer():
    data = position_map_pattern(SINGLE_TONE)
    for s in (1, 5, 9, 13):
        assert data[48 * (s - 1) + 6 : 48 * (s - 1) + 9] == bytes.fromhex("0e0981")
        assert data[768 + 16 * (s - 1) + 2] == 0xF0
    assert data[1024:] == FOOTER
    base = frame_of(synthetic_packets(patterns={1: SINGLE_TONE}))
    actual = frame_of(_replace_pattern_data(base, 1, data))
    checks = position_map_checks(base, actual)
    assert not checks.pop("source_is_verified_single_tone_body")
    assert all(checks.values())
    assert pattern_data(actual, 1) == data


def test_pattern_rejects_a_source_with_effects_or_extra_notes():
    with pytest.raises(ValueError, match="clear"):
        position_map_pattern(pattern_bytes([(1, 3, "0e0981", 0xF0)], footer=FOOTER))
    with pytest.raises(ValueError, match="single Sound3"):
        position_map_pattern(pattern_bytes([(1, 3, "0e0981", 0xF0), (2, 3, "0e0981", 0xF0)]))


def test_sequential_model_is_supported_by_rises_on_steps_5_and_13(tmp_path):
    write_loops(tmp_path / "seq.wav", {1: 0.0, 5: 0.4, 9: 0.0, 13: 0.4})
    tracks = note_tracks(tmp_path / "seq.wav")
    assert tracks["rejected_onsets_seconds"] == []
    results = step_results(tracks, REFERENCE)
    assert sorted(results) == [1, 5, 9, 13]
    assert {s: r["median"]["class"] for s, r in results.items()} == {
        1: "none",
        5: "effect",
        9: "none",
        13: "effect",
    }
    assert decide(results, PREDICTIONS)["classification"] == "sequential_high_nibble_first"


def test_all_flat_and_mixed_outcomes(tmp_path):
    write_loops(tmp_path / "flat.wav", {1: 0.0, 5: 0.0, 9: 0.0, 13: 0.0})
    flat = step_results(note_tracks(tmp_path / "flat.wav"), REFERENCE)
    assert decide(flat, PREDICTIONS)["classification"] == "effect_on_no_note_step"
    write_loops(tmp_path / "other.wav", {1: 0.4, 5: 0.0, 9: 0.0, 13: 0.4})
    other = step_results(note_tracks(tmp_path / "other.wav"), REFERENCE)
    assert decide(other, PREDICTIONS)["classification"] == "inconclusive"
