"""Register a device-side observation: the PO-33 records 16 tone bursts into drum Sound11.

Sound11 (sound ids 40..55) is empty in the verified Sound7-import state. The person plays
a generated WAV into the line input while holding RECORD + key 11, then takes a backup
without a restore. Hypotheses registered before the backup, from the existing Sound9
layout (16 references splitting a 64704-code recording into 4044-code windows):

- new_self_owned_buffer: exactly one new self-owned sample record appears
- sixteen_references: Sound11's 16 slice ids each gain a 9-byte reference to that buffer
- equal_split: the 16 windows are consecutive and equal, covering the recorded length
- everything_else_unchanged: all other sound records and pattern cells are unchanged
"""

import argparse
import io
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.packets import decode_artifact, sound_groups
from po33_re.modem.symbols import load_artifact

BASELINE_EXPERIMENT = "compiled-sound7-import-001"
DIRECTORY = "observe-drum11-record-001"
REGISTRATION = "drum11-record-registration-001.json"
SOUND11_IDS = list(range(40, 56))
RATE = 44100
LEAD_SECONDS, BURST_SECONDS, GAP_SECONDS, TAIL_SECONDS = 0.5, 0.1, 0.025, 0.3
LEVEL, FADE_SECONDS = 0.25, 0.005
FREQUENCIES = [round(400 * 2 ** (i / 8), 2) for i in range(16)]


def burst_wav():
    pieces = [np.zeros(round(LEAD_SECONDS * RATE))]
    t = np.arange(round(BURST_SECONDS * RATE)) / RATE
    fade = round(FADE_SECONDS * RATE)
    ramp = np.ones(len(t))
    ramp[:fade] = np.linspace(0, 1, fade)
    ramp[-fade:] = np.linspace(1, 0, fade)
    for frequency in FREQUENCIES:
        pieces.append(LEVEL * ramp * np.sin(2 * np.pi * frequency * t))
        pieces.append(np.zeros(round(GAP_SECONDS * RATE)))
    pieces.append(np.zeros(round(TAIL_SECONDS * RATE)))
    mono = np.concatenate(pieces)
    buffer = io.BytesIO()
    sf.write(buffer, np.column_stack((mono, mono)), RATE, subtype="PCM_16", format="WAV")
    return buffer.getvalue()


INSTRUCTIONS = """# Record 16 tone bursts into drum Sound 11

Sound 11 is empty. These steps sample a 2.8-second file of 16 short tone bursts into it.

1. Connect only the computer output to the PO-33 input; unplug the PO-33 output.
2. In a terminal, run the play command below. When it asks for Enter, first hold RECORD
   and key 11 on the PO-33, then press Enter. Keep holding until playback finishes,
   then release.
3. Swap the cables (PO-33 output to the computer), then run the backup session below.
   Do not play any pattern or move knobs before the backup.

```powershell
.\\.venv\\Scripts\\python.exe -m po33_re hw play experiments/observe-drum11-record-001/burst-source.wav
.\\.venv\\Scripts\\python.exe -m po33_re hw run experiments/observe-drum11-record-001
```

The session prints these steps again and asks you to press Enter once the recording is done.
"""


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    if folder.exists() or registration_path.exists():
        raise ValueError("Fresh folder and registration required")
    baseline_folder = root / "experiments" / BASELINE_EXPERIMENT
    observation = json.loads((baseline_folder / "hardware-observation-001.json").read_text())
    native = json.loads((baseline_folder / "hardware-recapture-results-001.json").read_text())
    baseline_path = baseline_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or sha256_file(baseline_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified Sound7-import state is required")
    groups = sound_groups(decode_artifact(load_artifact(baseline_path)))
    if any(groups.get(sid) for sid in SOUND11_IDS):
        raise ValueError("Sound11 must be empty in the baseline")
    folder.mkdir()
    source = folder / "burst-source.wav"
    write_bytes(source, burst_wav())
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "kind": "device_side_observation",
                "capture_status": "awaiting_hardware_session",
                "source_artifact": "../"
                + BASELINE_EXPERIMENT
                + "/derived/analysis-001/capture.symbols.npz",
                "registration": "../" + REGISTRATION,
                "observation_questions": [
                    "Did the PO-33 record normally, and roughly how long did you hold the buttons? (Enter to skip)"
                ],
                "hardware_restore": {"status": "not_applicable"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "drum11-record-registration-0.1",
                "hardware_verified": False,
                "registered_before_backup": True,
                "experiment_id": DIRECTORY,
                "baseline_artifact": baseline_path.relative_to(root).as_posix(),
                "baseline_artifact_sha256": native["artifact_sha256"],
                "source_wav": source.relative_to(root).as_posix(),
                "source_wav_sha256": sha256_file(source),
                "burst_frequencies_hz": FREQUENCIES,
                "burst_timing_seconds": {
                    "lead": LEAD_SECONDS,
                    "burst": BURST_SECONDS,
                    "gap": GAP_SECONDS,
                    "tail": TAIL_SECONDS,
                },
                "sound11_ids": SOUND11_IDS,
                "hypotheses": {
                    "new_self_owned_buffer": "exactly one new record longer than 9 bytes whose owner byte equals its own sound id",
                    "sixteen_references": "every Sound11 id 40..55 holds a 9-byte reference to that buffer's owner",
                    "equal_split": "the 16 windows are consecutive, equal within 1 code, and start at 0",
                    "everything_else_unchanged": "all other sound records and all pattern cells are unchanged",
                },
                "limits": [
                    "Observation of one device recording; button timing sets the recorded length",
                    "Which slice plays which burst is a later playback test",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "frequencies": FREQUENCIES}))


if __name__ == "__main__":
    main()
