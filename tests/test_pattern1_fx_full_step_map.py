import numpy as np
import soundfile as sf
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.formats.packets import decode_frame, encode_packets
from scripts.pattern1_fx_grid_pitch_method import note_tracks
from scripts.pattern1_fx_multi_step_pitch_method import decide, step_results
from scripts.prepare_pattern1_fx_full_step_map import (
    EFFECT_STEPS,
    FOOTER,
    PREDICTIONS,
    SETTINGS,
    edited_packets,
    full_map_checks,
    nibble_steps,
)

RATE = 44100
REFERENCE = 1190.417
SINGLE_TONE = pattern_bytes([(1, 3, "0e0981", 0xF0)])


def write_loops(path, effect_steps, loops=6, step_seconds=0.25):
    step = round(step_seconds * RATE)
    t = np.arange(round(0.21 * RATE)) / RATE
    loop = np.zeros(16 * step)
    for s in range(1, 17):
        rise = 0.4 if s in effect_steps else 0.0
        ratio = 1 + rise * np.minimum(t, 0.15) / 0.15
        tone = 0.3 * np.sin(2 * np.pi * np.cumsum(REFERENCE * ratio) / RATE)
        loop[(s - 1) * step : (s - 1) * step + len(tone)] += tone
    mono = np.r_[np.zeros(RATE), np.tile(loop, loops)]
    sf.write(path, np.column_stack((mono, mono)), RATE, subtype="PCM_16")


def test_footer_layout_and_predictions():
    assert nibble_steps(FOOTER, True) == list(EFFECT_STEPS)
    assert nibble_steps(FOOTER, False) == [1, 4, 5, 6, 9, 12, 13, 14]
    high = PREDICTIONS["sequential_high_nibble_first"]
    assert sorted(int(s) for s, c in high.items() if c == "effect") == list(EFFECT_STEPS)
    assert len(high) == 16


def test_edit_changes_only_pattern1_tempo_and_swing():
    frame = decode_frame(encode_packets(synthetic_packets(patterns={1: SINGLE_TONE})), start=0)
    actual = decode_frame(encode_packets(edited_packets(frame)), start=0)
    checks = full_map_checks(frame, actual)
    assert not checks.pop("source_is_verified_single_tone_body")
    assert all(checks.values())


def test_sixteen_notes_decide_the_sequential_model(tmp_path):
    write_loops(tmp_path / "seq.wav", EFFECT_STEPS)
    tracks = note_tracks(tmp_path / "seq.wav", SETTINGS)
    assert tracks["missing_grid_positions"] == []
    results = step_results(tracks, REFERENCE, SETTINGS)
    assert sorted(results) == list(range(1, 17))
    assert decide(results, PREDICTIONS, SETTINGS)["classification"] == (
        "sequential_high_nibble_first"
    )


def test_the_swapped_order_is_recognised_and_a_mismatch_is_inconclusive(tmp_path):
    write_loops(tmp_path / "low.wav", nibble_steps(FOOTER, False))
    low = step_results(note_tracks(tmp_path / "low.wav", SETTINGS), REFERENCE, SETTINGS)
    assert decide(low, PREDICTIONS, SETTINGS)["classification"] == "sequential_low_nibble_first"
    write_loops(tmp_path / "odd.wav", (2, 3, 5, 6, 10, 11, 13, 15))
    odd = step_results(note_tracks(tmp_path / "odd.wav", SETTINGS), REFERENCE, SETTINGS)
    assert decide(odd, PREDICTIONS, SETTINGS)["classification"] == "inconclusive"
