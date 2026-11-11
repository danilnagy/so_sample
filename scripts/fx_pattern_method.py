"""Frozen method: which pitch sounds at each step of a sixteen-pitch run, and how many onsets.

The first grid onset is the first rising crossing of the band-passed (150 to 6000 Hz),
3 ms maximum-filtered envelope above 15% of the recording's peak after the first 20 ms;
every later step follows the grid. For each step: the dominant frequency of two 40 ms Hann
windows, 100 and 180 ms after the grid onset; the level of each window in dB against the
reference step (the control pattern's step 1, window at 100 ms); and the number of onsets
in the step up to 10 ms before the next, rising crossings above 15% of the step's own envelope peak, at least 25 ms
apart, counting an onset at the grid start when the envelope is already above threshold.
"""

import numpy as np

from scripts.fx_descriptor_method import _dominant, _prepare

SETTINGS = {
    "band_hz": [150.0, 6000.0],
    "envelope_window_seconds": 0.003,
    "skip_seconds": 0.02,
    "onset_fraction": 0.15,
    "refractory_seconds": 0.025,
    "fft_size": 32768,
    "window_starts_ms": [100.0, 180.0],
    "window_ms": 40.0,
    "step_seconds": 0.25,
}


def describe_steps(path, first_step_times, reference, settings=SETTINGS):
    """first_step_times: grid onset of step 1 for each pattern; reference: (pattern index, step)."""
    mono, envelope, rate, _ = _prepare(path, settings)
    width = round(settings["window_ms"] / 1000 * rate)
    raw = []
    for start in first_step_times:
        steps = []
        for step in range(16):
            onset = start + step * settings["step_seconds"]
            windows = []
            for begin_ms in settings["window_starts_ms"]:
                a = round((onset + begin_ms / 1000) * rate)
                segment = mono[a : a + width]
                if len(segment) < width:
                    windows.append(None)
                    continue
                hz, prominence = _dominant(segment, rate, settings)
                windows.append(
                    {
                        "rms": float(np.sqrt(np.mean(segment**2))),
                        "hz": hz,
                        "prominence_db": prominence,
                    }
                )
            a = round(onset * rate)
            # Stop 10 ms early: the zero-phase band-pass smears the next note backwards.
            b = round((onset + settings["step_seconds"] - 0.01) * rate)
            env = envelope[a:b]
            peak = env.max() if len(env) else 0.0
            above = env > settings["onset_fraction"] * peak if peak else np.zeros(0, dtype=bool)
            rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
            if len(above) and above[0]:
                rising = np.r_[0, rising]
            onsets, last = 0, -np.inf
            for index in rising:
                if index - last >= settings["refractory_seconds"] * rate:
                    onsets += 1
                    last = index
            steps.append({"windows": windows, "onsets": onsets})
        raw.append(steps)
    ref = raw[reference[0]][reference[1] - 1]["windows"][0]["rms"]
    for steps in raw:
        for step in steps:
            for w in step["windows"]:
                if w is not None:
                    w["level_db"] = float(20 * np.log10(w["rms"] / ref + 1e-12))
                    del w["rms"]
    return raw
