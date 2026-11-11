"""Exploratory pitch tracks of the single-tone effect-order playbacks.

Written AFTER the registered single-tone F6/6F comparison returned inconclusive, so it
is exploratory and cannot decide that registered test. It tracks the dominant pitch in
20 ms windows every 10 ms from each loop's onset, takes the median over the first five
loops, and reports where the pitch departs from the unshifted reference.

Output: experiments/pattern1-single-tone-FX-order-pitch-track-exploratory-001.json
"""

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "pattern1-single-tone-FX-order-pitch-track-exploratory-001.json"
RECORDINGS = {
    "reference_no_FX": "edited-pattern1-single-tone-no-FX-001",
    "a_F6": "edited-pattern1-single-tone-FX-F6-001",
    "b_6F": "edited-pattern1-single-tone-FX-6F-001",
}
SETTINGS = {
    "band_hz": [600.0, 3500.0],
    "search_hz": [900.0, 2700.0],
    "window_seconds": 0.02,
    "hop_seconds": 0.01,
    "track_seconds": 0.4,
    "onset_fraction_of_peak": 0.15,
    "min_loop_gap_seconds": 1.0,
    "loops": 5,
    "fft_size": 32768,
    "departure_relative": 0.01,
    "step_seconds_at_100_bpm": 0.15,
}


def pitch_track(path, settings=SETTINGS):
    samples, rate = sf.read(path, always_2d=True)
    mono = samples.mean(axis=1)
    sos = butter(4, settings["band_hz"], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, mono)
    envelope = np.abs(mono)
    peak = envelope.max()
    above = np.flatnonzero(envelope > settings["onset_fraction_of_peak"] * peak)
    onsets = [int(above[0])]
    for index in above:
        if index - onsets[-1] > settings["min_loop_gap_seconds"] * rate:
            onsets.append(int(index))
    window = round(settings["window_seconds"] * rate)
    hop = round(settings["hop_seconds"] * rate)
    size = settings["fft_size"]
    freqs = np.fft.rfftfreq(size, 1 / rate)
    band = (freqs > settings["search_hz"][0]) & (freqs < settings["search_hz"][1])
    indices = np.flatnonzero(band)
    tracks, amplitudes = [], []
    for onset in onsets[: settings["loops"]]:
        row, amp = [], []
        for start in range(0, round(settings["track_seconds"] * rate), hop):
            segment = mono[onset + start : onset + start + window]
            spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
            k = indices[np.argmax(spectrum[band])]
            a, b, c = np.log(spectrum[k - 1 : k + 2] + 1e-12)
            delta = 0.5 * (a - c) / (a - 2 * b + c)
            row.append(float((k + delta) * rate / size))
            amp.append(float(np.abs(segment).max() / peak))
        tracks.append(row)
        amplitudes.append(amp)
    times = [round(i * settings["hop_seconds"] * 1000, 1) for i in range(len(tracks[0]))]
    return {
        "loop_onsets_seconds": [o / rate for o in onsets[: settings["loops"]]],
        "times_ms": times,
        "median_hz": np.median(tracks, axis=0).tolist(),
        "median_relative_amplitude": np.median(amplitudes, axis=0).tolist(),
    }


def departures(track, reference_hz, settings=SETTINGS):
    """Time spans where the median pitch is more than 1% from the reference while audible."""
    spans, current = [], None
    for t, hz, amp in zip(
        track["times_ms"], track["median_hz"], track["median_relative_amplitude"]
    ):
        off = amp > 0.2 and abs(hz / reference_hz - 1) > settings["departure_relative"]
        if off and current is None:
            current = [t, t]
        elif off:
            current[1] = t
        elif current is not None:
            spans.append(current)
            current = None
    if current is not None:
        spans.append(current)
    return spans


def main():
    output = ROOT / "experiments" / OUTPUT
    playbacks = {k: ROOT / "experiments" / d / "playback.wav" for k, d in RECORDINGS.items()}
    validate_outputs([output], list(playbacks.values()), False)
    tracks = {name: pitch_track(path) for name, path in playbacks.items()}
    reference_hz = float(np.median(tracks["reference_no_FX"]["median_hz"][:15]))
    result = {
        "analysis_version": "single-tone-FX-pitch-track-exploratory-0.1",
        "exploratory": True,
        "written_after_registered_result": "experiments/pattern1-single-tone-FX-order-comparison-001.json",
        "hardware_verified": False,
        "settings": SETTINGS,
        "playback_sha256": {name: sha256_file(path) for name, path in playbacks.items()},
        "reference_hz": reference_hz,
        "tracks": tracks,
        "departures_ms": {name: departures(t, reference_hz) for name, t in tracks.items()},
        "reading": (
            "A (F6) stays at the reference through step 1 and rises in step 2; "
            "B (6F) rises in step 1 and returns near the reference in step 2. Both fit step 1 "
            "= high nibble. The effect glides upward within a step rather than jumping an octave."
        ),
        "limits": [
            "Exploratory; method chosen after the data; does not change the registered inconclusive result",
            "Needs a registered time-resolved method and fresh recordings to become evidence",
        ],
    }
    write_bytes(output, json_bytes(result))
    print(json.dumps(result["departures_ms"], indent=2))


if __name__ == "__main__":
    main()
