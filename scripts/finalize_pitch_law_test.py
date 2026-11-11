"""Record the first pitch-law run: exact reception, early window caught a pitch glide.

The registered window (5..40 ms after each note) measured the glide from the previous
step's pitch, so the registered result is inconclusive. An exploratory track of each note
over time shows the pitch settling within about 35 ms at 100 cents per code; it is stored
separately and does not change the registered result.
"""

import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_pitch_law_test import DECISION
from scripts.pattern1_key_scale_grid_method import SETTINGS
from scripts.prepare_pitch_law_test import DIRECTORY, PITCH_CODES

ROOT = Path(__file__).resolve().parents[1]
OFFSETS_MS = [5, 15, 25, 35, 50, 70, 90, 120]


def pitch_over_time(path, loops=(1, 2, 3)):
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import butter, sosfiltfilt

    samples, rate = sf.read(str(path), always_2d=True)
    sos = butter(4, SETTINGS["band_hz"], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, samples.mean(axis=1))
    envelope = maximum_filter1d(np.abs(mono), 132)
    peak = envelope.max()
    above = envelope > 0.15 * peak
    first = (np.flatnonzero(above[1:] & ~above[:-1]) + 1)[0]
    size = 1 << 15
    freqs = np.fft.rfftfreq(size, 1 / rate)
    band = (freqs > 300) & (freqs < 7500)
    indices = np.flatnonzero(band)

    def pitch(segment):
        spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
        k = indices[np.argmax(spectrum[band])]
        a, b, c = np.log(spectrum[k - 1 : k + 2] + 1e-12)
        curvature = a - 2 * b + c
        return (k + (0.5 * (a - c) / curvature if curvature else 0.0)) * rate / size

    table = {}
    for step in range(16):
        rows = []
        for loop in loops:
            onset = first + (loop * 16 + step) * 0.25 * rate
            row = []
            for offset in OFFSETS_MS:
                start = int(onset + offset / 1000 * rate)
                segment = mono[start : start + int(0.02 * rate)]
                row.append(pitch(segment) if np.abs(segment).max() > 0.03 * peak else np.nan)
            rows.append(row)
        table[step + 1] = np.nanmedian(rows, axis=0)
    reference = table[1][OFFSETS_MS.index(50)]
    return {
        step: [None if np.isnan(v) else round(1200 * math.log2(v / reference), 1) for v in values]
        for step, values in table.items()
    }


def main():
    folder = ROOT / "experiments" / DIRECTORY
    decision_path = ROOT / "experiments" / DECISION
    native_path = folder / "hardware-recapture-results-001.json"
    observation_path = folder / "hardware-observation-001.json"
    exploratory_path = folder / "exploratory-pitch-over-time-001.json"
    validate_outputs([observation_path, exploratory_path], [native_path, decision_path], False)
    native = json.loads(native_path.read_text())
    decision = json.loads(decision_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    session = json.loads(session_path.read_text())
    tracks = pitch_over_time(folder / "playback.wav")
    settled = {str(step): values[OFFSETS_MS.index(50)] for step, values in tracks.items()}
    write_bytes(
        exploratory_path,
        json_bytes(
            {
                "analysis_version": "pitch-law-exploratory-pitch-over-time-0.1",
                "exploratory": True,
                "offsets_ms": OFFSETS_MS,
                "cents_by_step_over_time": {str(k): v for k, v in tracks.items()},
                "pitch_codes": PITCH_CODES,
                "predicted_cents": [100 * (c - 13) for c in PITCH_CODES],
                "settled_cents_at_50ms": settled,
            }
        ),
    )
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "pitch-law-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception of per-step pitch codes; registered "
                "early-window pitch decision inconclusive because each note glides from the "
                "previous pitch for about 25-35 ms",
                "native_check_passed": native["passed"] and all(native["checks"].values()),
                "registered_classification": decision["classification"],
                "decision_sha256": sha256_file(decision_path),
                "native_results_sha256": sha256_file(native_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "session_answers": [o for o in session["observations"] if o["answer"]],
                "exploratory_settled_cents_at_50ms": settled,
                "exploratory_sha256": sha256_file(exploratory_path),
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="validated_exact_native_pitch_glide_inconclusive",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"settled_cents_at_50ms": settled}))


if __name__ == "__main__":
    main()
