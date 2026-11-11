"""Frozen method: repetition period from a pitch track, scored by the mismatch fraction.

Same pitch track as scripts/fx_period_method.py (30 ms windows every 10 ms over 1.2 s).
A lag's score is the fraction of track pairs, at that lag, that differ by more than
50 cents. The period is the shortest lag, from 40 to 700 ms, whose score is within 0.05
of the best and whose half-lag region (30% to 70% of the lag) contains a lag scoring at
least 0.3: a repeating track mismatches itself half a period away, while a track that
merely changes slowly scores low at every short lag. A track with no such lag, or whose
best score is above 0.3, has no period by this score. A flat track (5th to 95th percentile
spread under 50 cents) with no period by this score falls back to the mean-difference
method of scripts/fx_period_method.py, which reads the period of the glitches themselves:
a retrigger or a very short loop on one segment shows only as periodic glitches.
"""

import numpy as np

from scripts.fx_period_method import SETTINGS as BASE_SETTINGS
from scripts.fx_period_method import period_ms as mean_period_ms
from scripts.fx_period_method import pitch_track

SETTINGS = {
    **BASE_SETTINGS,
    "mismatch_cents": 50.0,
    "max_mismatch": 0.3,
    "near_best": 0.05,
    "inner_mismatch": 0.3,
    "flat_spread_cents": 50.0,
}
for _key in ("max_mean_cents", "near_best_fraction", "near_best_cents"):
    SETTINGS.pop(_key)


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
        scores[lag] = float(np.mean(np.abs(a[keep] - b[keep]) > settings["mismatch_cents"]))
    if not scores:
        return None, None
    best = min(scores.values())
    if best > settings["max_mismatch"]:
        return None, best
    for lag in sorted(k for k, v in scores.items() if v <= best + settings["near_best"]):
        inner = [v for k, v in scores.items() if 0.3 * lag <= k <= 0.7 * lag]
        if inner and max(inner) >= settings["inner_mismatch"]:
            return lag * hop, scores[lag]
    core = values[~np.isnan(values)]
    if (
        len(core)
        and np.percentile(core, 95) - np.percentile(core, 5) < settings["flat_spread_cents"]
    ):
        return mean_period_ms(track, BASE_SETTINGS)
    return None, best


__all__ = ["SETTINGS", "period_ms", "pitch_track"]
