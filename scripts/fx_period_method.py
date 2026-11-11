"""Frozen method: the repetition period of a looping effect on a pitch-changing sample.

Sound6's sample rises through 599, 749, 899 and 1049 Hz at key 1. For a held note the
dominant frequency is tracked in 30 ms Hann windows every 10 ms from 20 ms to 1200 ms
after the grid onset, as a pitch track in cents. The track's period is the lag, from 40 to
700 ms, that minimises the mean absolute difference between the track and itself shifted
by that lag; among lags whose difference is within 25% plus 3 cents of the best, the
shortest wins, so multiples of the true period lose. A track whose best lag has a mean
difference above 60 cents has no period.
"""

import math

import numpy as np

from scripts.fx_descriptor_method import _dominant, _prepare

SETTINGS = {
    "band_hz": [150.0, 6000.0],
    "envelope_window_seconds": 0.003,
    "skip_seconds": 0.02,
    "onset_fraction": 0.15,
    "fft_size": 32768,
    "track_start_ms": 20.0,
    "track_end_ms": 1200.0,
    "hop_ms": 10.0,
    "window_ms": 30.0,
    "lag_range_ms": [40.0, 700.0],
    "near_best_fraction": 0.25,
    "near_best_cents": 3.0,
    "max_mean_cents": 60.0,
    "reference_hz": 400.0 * 2 ** (7 / 12),
}


def pitch_track(path, note_times, settings=SETTINGS):
    mono, _envelope, rate, _ = _prepare(path, settings)
    width = round(settings["window_ms"] / 1000 * rate)
    tracks = []
    for start in note_times:
        cents = []
        ms = settings["track_start_ms"]
        while ms <= settings["track_end_ms"]:
            a = round((start + ms / 1000) * rate)
            segment = mono[a : a + width]
            if len(segment) < width:
                cents.append(math.nan)
            else:
                hz, _ = _dominant(segment, rate, settings)
                cents.append(1200 * math.log2(hz / settings["reference_hz"]))
            ms += settings["hop_ms"]
        tracks.append(cents)
    return tracks


def period_ms(track, settings=SETTINGS):
    values = np.asarray(track, dtype=float)
    hop = settings["hop_ms"]
    low, high = (round(x / hop) for x in settings["lag_range_ms"])
    scores = {}
    for lag in range(low, high + 1):
        a, b = values[:-lag], values[lag:]
        keep = ~(np.isnan(a) | np.isnan(b))
        if keep.sum() < 10:
            continue
        scores[lag] = float(np.mean(np.abs(a[keep] - b[keep])))
    if not scores:
        return None, None
    best = min(scores.values())
    if best > settings["max_mean_cents"]:
        return None, best
    # Multiples of the true period match as well as the period itself: take the shortest
    # lag whose match is close to the best.
    threshold = best * (1 + settings["near_best_fraction"]) + settings["near_best_cents"]
    lag = min(k for k, v in scores.items() if v <= threshold)
    return lag * hop, scores[lag]
