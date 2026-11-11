"""Frozen method: does auditioning a sound after a pattern with locks follow the locks?

One playback recording holds three groups of hits of the same drum key, separated by
silences of over two seconds: auditions pressed by hand before the pattern, the
pattern's own notes (every one carrying a filter 63 lock, the bypass), and auditions
pressed by hand after the pattern stopped.

Hits are onsets of the band-passed, 3 ms maximum-filtered envelope rising past 10% of
its peak, at least 300 ms apart. For each hit a Hann window from 60 to 220 ms after the
onset is transformed, and the amplitude of harmonic h of the 200 Hz fundamental is the
spectral peak within 3 Hz of h * f0. A hit's response is 20 log10 of its harmonic
amplitudes over the median amplitudes of the pattern hits, so the pattern group is flat
at 0 dB by construction. Each hit and each group is classified as the filter law does:
silent (every harmonic below -40 dB), low_pass (top band at least 3 dB under the bottom
band), high_pass (the reverse) or flat.

Outcomes, from the two audition groups against the pattern reference:
- audition_follows_last_lock: the auditions before differ from the pattern, the ones
  after match it;
- audition_keeps_live_state: the auditions before and after match each other and both
  differ from the pattern;
- indistinguishable: all three groups match, so the live setting was already the bypass;
- other: anything else, with the reason.
"""

import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, sosfiltfilt

SETTINGS = {
    "band_hz": [100.0, 11000.0],
    "onset_fraction_of_peak": 0.10,
    "envelope_window_seconds": 0.003,
    "refractory_seconds": 0.3,
    "group_gap_seconds": 2.0,
    "window_ms": [60.0, 220.0],
    "fft_size": 65536,
    "fundamental_hz": 200.0,
    "harmonics": 50,
    "peak_search_hz": 3.0,
    "bottom_band": [1, 3],
    "top_band": [40, 50],
    "type_margin_db": 3.0,
    "same_margin_db": 3.0,
    "silent_db": -40.0,
    "expected_groups": ["before", "pattern", "after"],
    "min_hits_per_group": 3,
}

OUTCOMES = [
    "audition_follows_last_lock",
    "audition_keeps_live_state",
    "indistinguishable",
    "other",
]


def onsets(path, settings=SETTINGS):
    """Onset times in seconds, and the mono signal with its rate."""
    samples, rate = sf.read(str(path), always_2d=True)
    mono = samples.mean(axis=1)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    envelope = maximum_filter1d(
        np.abs(sosfiltfilt(sos, mono)), max(1, round(settings["envelope_window_seconds"] * rate))
    )
    above = envelope > settings["onset_fraction_of_peak"] * envelope.max()
    rising = np.flatnonzero(above[1:] & ~above[:-1]) + 1
    if above[0]:
        raise ValueError("The recording must start in silence before the first hit")
    refractory = settings["refractory_seconds"] * rate
    kept = []
    for index in rising:
        if not kept or index - kept[-1] >= refractory:
            kept.append(int(index))
    return [k / rate for k in kept], mono, rate


def groups_of(times, settings=SETTINGS):
    """Hit indices grouped where the gap to the previous hit exceeds the group gap."""
    groups, current = [], []
    for i, t in enumerate(times):
        if current and t - times[i - 1] > settings["group_gap_seconds"]:
            groups.append(current)
            current = []
        current.append(i)
    if current:
        groups.append(current)
    return groups


def harmonic_amplitudes(mono, rate, times, settings=SETTINGS):
    """Array [hit, harmonic] of amplitudes; a hit too close to the end is NaN."""
    size = settings["fft_size"]
    freqs = np.fft.rfftfreq(size, 1 / rate)
    f0, count = settings["fundamental_hz"], settings["harmonics"]
    begin_ms, end_ms = settings["window_ms"]
    amplitudes = np.full((len(times), count), np.nan)
    for n, t in enumerate(times):
        begin, end = round((t + begin_ms / 1000) * rate), round((t + end_ms / 1000) * rate)
        segment = mono[begin:end]
        if len(segment) < end - begin:
            continue
        spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
        for h in range(1, count + 1):
            near = np.abs(freqs - h * f0) <= settings["peak_search_hz"]
            amplitudes[n, h - 1] = spectrum[near].max()
    return amplitudes


def band_means(response, settings=SETTINGS):
    lo, hi = settings["bottom_band"]
    top_lo, top_hi = settings["top_band"]
    return float(np.mean(response[lo - 1 : hi])), float(np.mean(response[top_lo - 1 : top_hi]))


def classify(response, settings=SETTINGS):
    if np.all(response < settings["silent_db"]):
        return "silent"
    bottom, top = band_means(response, settings)
    if top <= bottom - settings["type_margin_db"]:
        return "low_pass"
    if bottom <= top - settings["type_margin_db"]:
        return "high_pass"
    return "flat"


def same(a, b, settings=SETTINGS):
    """Two band-mean pairs agree within the margin in both bands."""
    return all(abs(x - y) < settings["same_margin_db"] for x, y in zip(a, b, strict=True))


def analyze(path, settings=SETTINGS):
    """Measure one recording: hits, groups, per-group responses and the outcome."""
    times, mono, rate = onsets(path, settings)
    amplitudes = harmonic_amplitudes(mono, rate, times, settings)
    groups = groups_of(times, settings)
    report = {
        "hit_times_seconds": times,
        "groups": [[times[i] for i in g] for g in groups],
        "group_sizes": [len(g) for g in groups],
    }
    expected = settings["expected_groups"]
    if len(groups) != len(expected):
        report.update(
            outcome="other", reason=f"{len(groups)} groups of hits, {len(expected)} expected"
        )
        return report
    if any(len(g) < settings["min_hits_per_group"] for g in groups):
        report.update(outcome="other", reason="a group has too few hits")
        return report
    pattern = groups[expected.index("pattern")]
    valid = [i for i in pattern if not np.isnan(amplitudes[i]).any()]
    reference = np.median(amplitudes[valid], axis=0)
    with np.errstate(divide="ignore"):
        response = 20 * np.log10(amplitudes / reference)
    summary = {}
    for name, members in zip(expected, groups, strict=True):
        rows = [response[i] for i in members if not np.isnan(response[i]).any()]
        median = np.median(rows, axis=0)
        summary[name] = {
            "hits": len(members),
            "types": [classify(r, settings) for r in rows],
            "type": classify(median, settings),
            "band_means_db": band_means(median, settings),
            "median_response_db": [round(float(v), 2) for v in median],
        }
    report["groups_by_name"] = summary
    flat = (0.0, 0.0)
    before_same = same(summary["before"]["band_means_db"], flat, settings)
    after_same = same(summary["after"]["band_means_db"], flat, settings)
    before_after = same(
        summary["before"]["band_means_db"], summary["after"]["band_means_db"], settings
    )
    if before_same and after_same:
        outcome = "indistinguishable"
    elif not before_same and after_same:
        outcome = "audition_follows_last_lock"
    elif before_after and not after_same:
        outcome = "audition_keeps_live_state"
    else:
        outcome = "other"
    report.update(
        outcome=outcome,
        comparisons={
            "before_matches_pattern": before_same,
            "after_matches_pattern": after_same,
            "before_matches_after": before_after,
        },
        live_filter_before_pattern=summary["before"]["type"],
        live_filter_after_pattern=summary["after"]["type"],
    )
    if outcome == "other":
        report["reason"] = (
            "the audition groups neither follow the pattern's locks nor agree with each other"
        )
    return report
