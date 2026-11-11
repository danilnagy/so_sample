import numpy as np
import pytest

from po33_re.analysis.serialization import as_words, feedback, feedback_probe, packed_view


def test_known_serialization_orders():
    left = np.array([0, 1, 2, 3], dtype=np.uint8)
    right = np.array([3, 2, 1, 0], dtype=np.uint8)
    assert packed_view(left, right, (0, 1, 2, 3), 0, "left").tolist() == [228]
    assert packed_view(left, right, (0, 1, 2, 3), 0, "stereo_bytes").tolist() == [228, 27]
    assert packed_view(left, right, (0, 1, 2, 3), 0, "stereo_symbols").tolist() == [156, 54]


@pytest.mark.parametrize("width", [1, 2, 4, 8])
def test_unsigned_feedback_recovers_injected_cumulative_words(width):
    # Construct the fixture with Python modular integers, independently of NumPy feedback.
    mask = (1 << (8 * width)) - 1
    plain = [mask, 3, mask - 1, 9, 0, 2]
    encoded, state = [], 0
    for value in plain:
        state = (state + value) & mask
        encoded.append(state)
    words = np.array(encoded, dtype="u" + str(width))
    assert feedback(words, 1, "subtract_mod_word").tolist() == plain[1:]
    state, encoded_xor = 0, []
    for value in plain:
        state ^= value
        encoded_xor.append(state)
    assert feedback(np.array(encoded_xor, dtype="u" + str(width)), 1, "xor").tolist() == plain[1:]


def test_word_endianness_and_partial_analysis_tail():
    values = np.array([1, 2, 3, 4, 5], dtype=np.uint8)
    assert as_words(values, 2, "little").tolist() == [513, 1027]
    assert as_words(values, 2, "big").tolist() == [258, 772]


def unpack(values):
    return ((values[:, None] >> np.array([0, 2, 4, 6])) & 3).astype(np.uint8).ravel()


def test_feedback_search_finds_injected_offset_and_checks_holdout():
    rng = np.random.default_rng(74)
    x = rng.integers(0, 256, 4096, dtype=np.uint8)
    y = x + np.uint8(7)
    # Identity serialization plus modular lag-1 subtraction explains the constant offset.
    train_a, train_b = [unpack(v) for v in (x[:2048], y[:2048])]
    hold_a, hold_b = [unpack(v) for v in (x[2048:], y[2048:])]
    result = feedback_probe(
        [train_a, train_a],
        [train_b, train_b],
        [hold_a, hold_a],
        [hold_b, hold_b],
        "left",
        1,
        "little",
    )
    assert result["candidates_tested"] == 1920
    assert result["best_training_candidate"]["training_match_fraction"] == 1
    assert result["holdout_match_fraction"] == 1
    # Destroy the holdout relation while keeping training fixed.
    bad = unpack(rng.integers(0, 256, 2048, dtype=np.uint8))
    result = feedback_probe(
        [train_a, train_a], [train_b, train_b], [hold_a, hold_a], [bad, bad], "left", 1, "little"
    )
    assert result["best_training_candidate"]["training_match_fraction"] == 1
    assert result["holdout_match_fraction"] < 0.1


def test_invalid_feedback_and_packing():
    values = np.array([0, 1, 2, 3], dtype=np.uint8)
    with pytest.raises(ValueError):
        packed_view(values, values, (0, 1, 1, 3), 0, "left")
    with pytest.raises(ValueError):
        feedback(values, len(values), "xor")
    with pytest.raises(ValueError):
        as_words(values, 3, "little")
