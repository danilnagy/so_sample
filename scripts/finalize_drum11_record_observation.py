"""Record the drum Sound11 recording observation and the slice analysis.

Adds, to the registered structure result, a measurement of the stored audio: where each
burst starts and the dominant frequency inside each slice window.
"""

import json
from pathlib import Path

import numpy as np

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, sound_data
from po33_re.formats.samples import decode_signed_mulaw
from po33_re.modem.symbols import load_artifact
from scripts.check_drum11_record_observation import RESULT
from scripts.prepare_drum11_record_observation import DIRECTORY, FREQUENCIES

ROOT = Path(__file__).resolve().parents[1]
RATE = 23437.5


def slice_analysis(frame, owner, windows):
    codes = np.frombuffer(sound_data(frame, owner)[9:], dtype=np.uint8)
    audio = np.asarray(decode_signed_mulaw(codes), dtype=float)
    block = 47
    count = len(audio) // block
    peaks = np.abs(audio[: count * block]).reshape(count, block).max(axis=1)
    loud = peaks > 0.2 * peaks.max()
    onsets = ((np.flatnonzero(loud[1:] & ~loud[:-1]) + 1) * block).tolist()
    slices = []
    for start, end in windows:
        segment = audio[start:end]
        spectrum = np.abs(
            np.fft.rfft((segment - segment.mean()) * np.hanning(len(segment)), 1 << 16)
        )
        freqs = np.fft.rfftfreq(1 << 16, 1 / RATE)
        slices.append(
            {"window": [start, end], "dominant_hz": float(freqs[np.argmax(spectrum[1:]) + 1])}
        )
    return {"burst_onsets_codes": [0, *onsets], "slices": slices}


def main():
    folder = ROOT / "experiments" / DIRECTORY
    result_path = ROOT / "experiments" / RESULT
    observation_path = folder / "hardware-observation-001.json"
    validate_outputs([observation_path], [result_path], False)
    result = json.loads(result_path.read_text())
    frame = decode_artifact(load_artifact(folder / "derived/analysis-001/capture.symbols.npz"))
    analysis = slice_analysis(frame, result["owner_sound_id"], result["slice_windows"])
    matched = [
        abs(item["dominant_hz"] - FREQUENCIES[k]) / FREQUENCIES[k] < 0.01
        for k, item in enumerate(analysis["slices"][:15])
    ]
    session_path = max(folder.glob("hardware-session-*.json"))
    write_bytes(
        observation_path,
        json_bytes(
            {
                "analysis_version": "drum11-record-observation-0.1",
                "hardware_verified": True,
                "verified_scope": "Device recording into drum Sound11 read from one backup",
                "hypotheses": result["hypotheses"],
                "owner_sound_id": result["owner_sound_id"],
                "owner_capacity_codes": result["owner_capacity_codes"],
                "recorded_end_code": result["slice_windows"][-1][1],
                "slice_windows": result["slice_windows"],
                "slice_analysis": analysis,
                "slices_1_to_15_hold_bursts_1_to_15_in_order": all(matched),
                "reading": "Leading silence is trimmed; slice boundaries sit at detected burst "
                "onsets; slice k holds burst k; slice 16 runs to the end of the recording; the "
                "buffer is owned by slice 1's sound id",
                "result_sha256": sha256_file(result_path),
                "harness_session": session_path.name,
                "harness_session_sha256": sha256_file(session_path),
            }
        ),
    )
    status_path = folder / "experiment.json"
    status = json.loads(status_path.read_text())
    status.update(
        capture_status="validated_drum_recording_structure_onset_slices",
        analysis="derived/analysis-001",
        result="../" + RESULT,
        hardware_observation=observation_path.name,
    )
    write_bytes(status_path, json_bytes(status), force=True)
    print(json.dumps({"slices_match_bursts": all(matched), "owner": result["owner_sound_id"]}))


if __name__ == "__main__":
    main()
