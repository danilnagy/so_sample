"""Record the first keyboard scale map run: exact reception, playback at the wrong tempo.

The backup matched the target (60 BPM), but the playback ran at 80 BPM (16 steps of
187.5 ms, a 3.0 s loop), so the registered 250 ms grid missed most notes and the decision
is other_or_inconclusive. An exploratory reading on an 80 BPM grid is stored separately.
"""

import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from scripts.check_pattern1_key_scale_map import DECISION
from scripts.prepare_pattern1_key_scale_map import DIRECTORY

ROOT = Path(__file__).resolve().parents[1]
FIRST_ONSET_SECONDS = 1.325
STEP_SECONDS_80_BPM = 0.1875
LOOP_SECONDS = 16 * STEP_SECONDS_80_BPM


def grid_cents(path, reference_hz, loops=4):
    samples, rate = sf.read(str(path), always_2d=True)
    sos = butter(4, [300, 8000], btype="band", fs=rate, output="sos")
    mono = sosfiltfilt(sos, samples.mean(axis=1))
    size = 1 << 15
    freqs = np.fft.rfftfreq(size, 1 / rate)
    band = (freqs > 300) & (freqs < 7500)
    table = []
    for loop in range(loops):
        row = []
        for step in range(16):
            start = round(
                (FIRST_ONSET_SECONDS + loop * LOOP_SECONDS + step * STEP_SECONDS_80_BPM + 0.008)
                * rate
            )
            segment = mono[start : start + round(0.02 * rate)]
            spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), size))
            k = np.flatnonzero(band)[np.argmax(spectrum[band])]
            row.append(1200 * math.log2(freqs[k] / reference_hz))
        table.append(row)
    return np.median(table, axis=0).tolist(), table


def main():
    folder = ROOT / "experiments" / DIRECTORY
    decision_path = ROOT / "experiments" / DECISION
    observation_path = folder / "hardware-observation-001.json"
    exploratory_path = folder / "exploratory-80bpm-grid-cents-001.json"
    native_path = folder / "hardware-recapture-results-001.json"
    validate_outputs([observation_path, exploratory_path], [native_path, decision_path], False)
    native = json.loads(native_path.read_text())
    decision = json.loads(decision_path.read_text())
    session_path = max(folder.glob("hardware-session-*.json"))
    median, loops = grid_cents(folder / "playback.wav", 1190.4169592315686)
    write_bytes(
        exploratory_path,
        json_bytes(
            {
                "analysis_version": "key-scale-exploratory-80bpm-grid-0.1",
                "exploratory": True,
                "reason": "Playback ran at 80 BPM instead of the restored 60 BPM",
                "playback_sha256": sha256_file(folder / "playback.wav"),
                "grid": {
                    "first_onset_seconds": FIRST_ONSET_SECONDS,
                    "step_seconds": STEP_SECONDS_80_BPM,
                    "measure_offset_seconds": [0.008, 0.028],
                },
                "median_cents_by_key": [round(c, 1) for c in median],
                "loops_cents": [[round(c, 1) for c in row] for row in loops],
            }
        ),
    )
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "key-scale-map-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Exact native reception of key s on step s; registered "
                "pitch decision inconclusive because playback ran at 80 BPM",
                "native_check_passed": native["passed"] and all(native["checks"].values()),
                "registered_classification": decision["classification"],
                "decision_sha256": sha256_file(decision_path),
                "native_results_sha256": sha256_file(native_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
                "exploratory_median_cents_by_key": [round(c) for c in median],
                "exploratory_sha256": sha256_file(exploratory_path),
                "lessons": [
                    "The tempo changed between the backup and the playback; keep BPM untouched",
                    "Low keys play long and a new note cuts the previous one, so onsets must come from the step grid, not silence gaps",
                    "The lowest keys sit near 400 Hz, below the registered search floor",
                ],
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="validated_exact_native_playback_wrong_tempo_inconclusive",
        hardware_restore={"status": "verified_exact_native_target"},
        analysis="derived/analysis-001",
        native_results=native_path.name,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"exploratory_cents": [round(c) for c in median]}))


if __name__ == "__main__":
    main()
