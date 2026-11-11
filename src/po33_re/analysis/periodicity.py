"""Exact repeat and lag-similarity measurements in diagnostic phase values."""

import numpy as np
from scipy.fft import irfft, next_fast_len, rfft

from ..modem.symbols import validate_symbols


def lag_similarity(values, max_lag=2048):
    validate_symbols(values)
    if type(max_lag) is not int or not 0 < max_lag < len(values):
        raise ValueError("Lag must be positive and shorter than the window")
    count = len(values)
    size = next_fast_len(2 * count - 1)
    one_hot = np.eye(4)[values].T
    spectra = rfft(one_hot, n=size, axis=1)
    matches = irfft(np.sum(spectra * spectra.conj(), axis=0), n=size)[1 : max_lag + 1]
    return np.clip(matches / (count - np.arange(1, max_lag + 1)), 0, 1)


def lag_runs(values, lag, window_start=8192, limit=8):
    validate_symbols(values)
    if (
        type(lag) is not int
        or not 0 < lag < len(values)
        or not 0 <= window_start < len(values) - lag
    ):
        raise ValueError("Invalid lag/run search window")
    if type(limit) is not int or limit <= 0:
        raise ValueError("Positive run report limit required")
    equal = values[window_start:-lag] == values[window_start + lag :]
    edges = np.diff(np.r_[0, equal, 0].astype(np.int8))
    starts = np.flatnonzero(edges == 1) + window_start
    ends = np.flatnonzero(edges == -1) + window_start
    order = np.argsort(ends - starts)[-limit:][::-1]
    return [
        {
            "equal_comparison_span": [int(starts[i]), int(ends[i])],
            "covered_value_span": [int(starts[i]), int(ends[i] + lag)],
            "matching_lag_pairs": int(ends[i] - starts[i]),
        }
        for i in order
    ]


def smallest_period(values, max_period=2048):
    validate_symbols(values)
    if type(max_period) is not int or not 0 < max_period < len(values):
        raise ValueError("Invalid period bound")
    return next(
        (p for p in range(1, max_period + 1) if np.array_equal(values[p:], values[:-p])), None
    )
