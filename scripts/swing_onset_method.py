"""Frozen method: onset times of short clicks on every step, and the even-step delay.

The band-passed signal's 3 ms maximum-filtered envelope is thresholded at 15% of the
peak of its first two seconds after the noise floor; the onset search skips the first 20 ms.
An onset is a rising crossing at least 40 ms after the previous one; at swing 18 the even
click can land 64 ms before the next odd one. Onsets are assigned
to steps in order from the first, 16 per loop. For each even step, the position is
(t_even - t_odd_before) / (t_odd_after - t_odd_before): 0.5 when straight, larger when
the even step is delayed. The delay in steps is 2 * (position - 0.5).
"""

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [300.0, 4000.0],
    "envelope_window_seconds": 0.003,
    "skip_seconds": 0.02,
    "threshold_fraction": 0.15,
    "refractory_seconds": 0.04,
    "steps_per_loop": 16,
    "loops": 5,
}


def onsets(path, settings=SETTINGS):
    samples, rate = sf.read(str(path), always_2d=True)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    envelope = maximum_filter1d(
        np.abs(sosfiltfilt(sos, samples.mean(axis=1))),
        max(1, round(settings["envelope_window_seconds"] * rate)),
    )
    envelope[: round(settings["skip_seconds"] * rate)] = 0.0
    threshold = settings["threshold_fraction"] * envelope.max()
    above = envelope > threshold
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    kept, last = [], -np.inf
    for index in rising:
        if index - last >= settings["refractory_seconds"] * rate:
            kept.append(index / rate)
            last = index
    return kept


def even_step_positions(times, settings=SETTINGS):
    """Per loop, the position of each even step between its odd neighbours."""
    per_loop = settings["steps_per_loop"]
    result = []
    for loop in range(settings["loops"]):
        base = loop * per_loop
        if base + per_loop >= len(times):
            break
        positions = {}
        for even in range(2, per_loop + 1, 2):
            before, after = times[base + even - 2], times[base + even]
            positions[even] = (times[base + even - 1] - before) / (after - before)
        result.append(positions)
    return result


def summarize(times, settings=SETTINGS):
    loops = even_step_positions(times, settings)
    values = [p for positions in loops for p in positions.values()]
    step_seconds = [(times[b + 16] - times[b]) / 16 for b in range(0, len(times) - 16, 16)][
        : settings["loops"]
    ]
    return {
        "onset_count": len(times),
        "loops_measured": len(loops),
        "positions_by_loop": [{str(k): v for k, v in p.items()} for p in loops],
        "median_position": float(np.median(values)) if values else None,
        "position_spread": float(np.max(values) - np.min(values)) if values else None,
        "median_step_seconds": float(np.median(step_seconds)) if step_seconds else None,
    }
