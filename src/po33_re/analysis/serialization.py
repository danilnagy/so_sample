"""Bounded serialization/feedback probes; these words are not a state image."""

from itertools import permutations

import numpy as np

from ..modem.symbols import validate_symbols

LAGS = (1, 2, 3, 4, 8, 16, 24, 32, 64, 128)


def packed_view(left, right, mapping, offset, layout):
    validate_symbols(left)
    validate_symbols(right)
    if sorted(mapping) != [0, 1, 2, 3] or offset not in range(4):
        raise ValueError("Invalid label permutation or packing offset")
    count = (min(len(left), len(right)) - offset) // 4 * 4
    if count <= 0:
        raise ValueError("Insufficient shared labels for packing")
    lut = np.asarray(mapping, dtype=np.uint8)
    a, b = [lut[s[offset : offset + count]] for s in (left, right)]
    weights = np.array([1, 4, 16, 64], dtype=np.uint16)

    def pack(s):
        return np.sum(s.reshape(-1, 4).astype(np.uint16) * weights, axis=1).astype(np.uint8)

    if layout == "left":
        return pack(a)
    if layout == "right":
        return pack(b)
    if layout == "stereo_symbols":
        return pack(np.column_stack((a, b)).ravel())
    if layout == "stereo_bytes":
        return np.column_stack((pack(a), pack(b))).ravel()
    raise ValueError("Unknown serialization layout")


def as_words(values, width, endian):
    if width not in (1, 2, 4, 8) or endian not in ("little", "big"):
        raise ValueError("Unsupported word width or endianness")
    if not isinstance(values, np.ndarray) or values.dtype != np.uint8 or values.ndim != 1:
        raise ValueError("Expected one-dimensional uint8 packed bytes")
    count = len(values) // width * width
    if count == 0:
        raise ValueError("Insufficient bytes for a word")
    dtype = np.dtype(("<" if endian == "little" else ">") + "u" + str(width))
    return np.frombuffer(values[:count].tobytes(), dtype=dtype).astype(np.dtype("u" + str(width)))


def feedback(words, lag, mode):
    if type(lag) is not int or not 0 < lag < len(words):
        raise ValueError("Lag must be positive and shorter than the word stream")
    if mode == "xor":
        return words[lag:] ^ words[:-lag]
    if mode == "subtract_mod_word":
        # Unsigned NumPy subtraction wraps at the declared word width.
        return words[lag:] - words[:-lag]
    raise ValueError("Unknown feedback model")


def feedback_probe(train_a, train_b, holdout_a, holdout_b, layout, width, endian):
    best = None
    tested = 0
    for mapping in permutations(range(4)):
        for offset in range(4):
            x, y = [
                as_words(packed_view(*pair, mapping, offset, layout), width, endian)
                for pair in (train_a, train_b)
            ]
            for lag in LAGS:
                for mode in ("xor", "subtract_mod_word"):
                    dx, dy = feedback(x, lag, mode), feedback(y, lag, mode)
                    matches = int(np.count_nonzero(dx == dy))
                    candidate = {
                        "mapping": list(mapping),
                        "offset_symbols": offset,
                        "lag_words": lag,
                        "mode": mode,
                        "training_words": len(dx),
                        "training_matches": matches,
                        "training_match_fraction": matches / len(dx),
                    }
                    tested += 1
                    if (
                        best is None
                        or candidate["training_match_fraction"] > best["training_match_fraction"]
                    ):
                        best = candidate
    x, y = [
        as_words(packed_view(*pair, best["mapping"], best["offset_symbols"], layout), width, endian)
        for pair in (holdout_a, holdout_b)
    ]
    dx, dy = [feedback(v, best["lag_words"], best["mode"]) for v in (x, y)]
    matches = int(np.count_nonzero(dx == dy))
    return {
        "layout": layout,
        "word_bytes": width,
        "endian": endian,
        "candidates_tested": tested,
        "best_training_candidate": best,
        "holdout_words": len(dx),
        "holdout_matches": matches,
        "holdout_match_fraction": matches / len(dx),
        "training_selected_then_holdout": True,
    }
