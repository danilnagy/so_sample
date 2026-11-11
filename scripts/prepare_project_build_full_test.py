"""Register the full project build: every slot and every pattern from one spec.

The first project build used two imports and two patterns (docs/project-build-results.md).
This one fills the device: eight melodic imports, eight drum kits, sixteen patterns with
notes, locks and effects, a chain of eight entries, tempo 128 and swing 6, all from one
spec through po33_re.project_build.

Melodic slot s gets a 0.3 s tone at 220 * 2^((s-1)/12) Hz. Drum kit N gets sixteen 43 ms
tones at 150 * N * 2^((k-1)/12) Hz. Every pattern p has Sound13 key 1 on steps 1, 5, 9
and 13, Sound 14 key 1 on steps 5 and 13 of pattern 1 only, a melody on Sound (p mod 8) + 1,
hats on Sound 11, and an effect on step 16. Chain 1..8.

Models registered before the session (frozen methods swing_onset_method and
polyphony_method_exploratory): exact reception; tempo_128: Sound13 onsets 4 steps apart,
0.469 s within 5 ms; chain_8: Sound14 bursts recur every chain cycle, 8 * 16 steps =
15.0 s within 20 ms; melody_first_note: pattern 1's melody sound at key 1 sounds in step
1 and not in step 2 by 20 dB.
"""

import argparse
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import decode_artifact
from po33_re.formats.patterns import drum_notes, melodic_notes
from po33_re.modem.symbols import load_artifact
from po33_re.project_build import build_project
from scripts.polyphony_method_exploratory import SETTINGS as LEVEL_BASE
from scripts.prepare_drum_kit_import_test import hit_wav
from scripts.prepare_fx_onsets_120_observation import DIRECTORY as SOURCE_EXPERIMENT
from scripts.swing_onset_method import SETTINGS as ONSET_BASE

TEMPO, SWING, CHAIN = 128, 6, [1, 2, 3, 4, 5, 6, 7, 8]
STEP_SECONDS = 60 / TEMPO / 4
MELODIC_HZ = {s: 220.0 * 2 ** ((s - 1) / 12) for s in range(1, 9)}
MELODIC_CODES = 7031
DRUM_BASE_HZ = {n: 150.0 * n for n in range(9, 17)}
DRUM_CODES = 1000
KICK = [1 if s in (1, 5, 9, 13) else None for s in range(1, 17)]
SNARE = [1 if s in (5, 13) else None for s in range(1, 17)]
HATS = [1 if s % 2 == 0 else None for s in range(1, 17)]
MELODY = [1, None, 3, None, 5, None, 8, None, 1, None, 3, None, 5, None, 8, None]
SOURCE_DIRECTORY = "project-build-full-source-001"
BUILD_DIRECTORY = "project-build-full-001"
DIRECTORY = "project-build-full-001/compiled"
REGISTRATION = "project-build-full-registration-001.json"
PLAYBACK_SECONDS = 36


def melody_sound(pattern):
    return (pattern - 1) % 8 + 1


def spec(sources):
    patterns = {}
    for p in range(1, 17):
        notes = {str(melody_sound(p)): MELODY, "13": KICK, "11": HATS}
        if p == 1:
            notes["14"] = SNARE
        patterns[str(p)] = {
            "notes": notes,
            "parameters": {str(melody_sound(p)): {"filter": 63 if p % 2 else 30, "resonance": 1}},
            "locks": {"11": {"volume": [None] * 15 + [24]}},
            "effects": [None] * 15 + [(p - 1) % 15 + 1],
        }
    return {
        "tempo": TEMPO,
        "swing": SWING,
        "chain": CHAIN,
        "melodic": {str(s): str(sources / f"melodic{s}.wav") for s in range(1, 9)},
        "drums": {
            str(n): [str(sources / f"kit{n}-key{k:02d}.wav") for k in range(1, 17)]
            for n in range(9, 17)
        },
        "patterns": patterns,
    }


KICK_HZ = DRUM_BASE_HZ[13]
SNARE_HZ = DRUM_BASE_HZ[14]
ONSET_KICK = {
    **ONSET_BASE,
    "band_hz": [KICK_HZ * 0.9, KICK_HZ * 1.1],
    "steps_per_loop": 4,
    "loops": 10,
}
ONSET_SNARE = {
    **ONSET_BASE,
    "band_hz": [SNARE_HZ * 0.9, SNARE_HZ * 1.1],
    "steps_per_loop": 2,
    "loops": 10,
}
LEVEL_SETTINGS = {**LEVEL_BASE, "step_seconds": STEP_SECONDS, "window_ms": [60.0, 110.0]}
MELODY_KEY1_HZ = MELODIC_HZ[1] * 2 ** (7 / 12)
EXPECTED = {
    "kick_interval_s": 4 * STEP_SECONDS,
    "chain_cycle_s": len(CHAIN) * 16 * STEP_SECONDS,
}
TOLERANCES = {"kick_s": 0.005, "cycle_s": 0.02, "melody_db": 20.0}
QUESTION = "Did it sound like a full beat that changed melody sound each pattern? (Enter to skip)"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    experiments = root / "experiments"
    registration_path = experiments / REGISTRATION
    if registration_path.exists() or any(
        (experiments / name).exists() for name in (SOURCE_DIRECTORY, BUILD_DIRECTORY)
    ):
        raise ValueError("Fresh folders and registration required")
    source_folder = experiments / SOURCE_EXPERIMENT
    observation = json.loads((source_folder / "hardware-observation-001.json").read_text())
    native = json.loads((source_folder / "hardware-recapture-results-001.json").read_text())
    source_path = source_folder / "derived/analysis-001/capture.symbols.npz"
    if (
        not observation["hardware_verified"]
        or not observation["hypotheses"]["exact_reception"]
        or sha256_file(source_path) != native["artifact_sha256"]
    ):
        raise ValueError("The verified FX onsets state is required")
    sources = experiments / SOURCE_DIRECTORY
    sources.mkdir()
    for s, hz in MELODIC_HZ.items():
        write_bytes(sources / f"melodic{s}.wav", hit_wav(hz, MELODIC_CODES))
    for n, base in DRUM_BASE_HZ.items():
        for k in range(1, 17):
            write_bytes(
                sources / f"kit{n}-key{k:02d}.wav", hit_wav(base * 2 ** ((k - 1) / 12), DRUM_CODES)
            )
    project = spec(Path("experiments") / SOURCE_DIRECTORY)
    report = build_project(source_path, project, experiments / BUILD_DIRECTORY)
    if not report["passed"]:
        raise ValueError("Project build failed its software checks")
    folder = experiments / DIRECTORY
    target = decode_artifact(load_artifact(folder / "edited.symbols.npz"))
    checks = [
        all(melodic_notes(target, p, melody_sound(p)) == MELODY for p in range(1, 17)),
        all(drum_notes(target, p, 13) == KICK for p in range(1, 17)),
        drum_notes(target, 1, 14) == SNARE and drum_notes(target, 2, 14) == [None] * 16,
        pattern_chain(target) == CHAIN,
        tempo(target) == TEMPO,
        swing(target) == SWING,
    ]
    if not all(checks):
        raise ValueError(f"Compiled target is not as planned: {checks}")
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../../" + REGISTRATION,
                "build_report": "../build-report.json",
                "playback_seconds": PLAYBACK_SECONDS,
                "observation_questions": [QUESTION],
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "project-build-full-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "source_artifact": source_path.relative_to(root).as_posix(),
                "source_artifact_sha256": native["artifact_sha256"],
                "source_capture_sha256": native["capture_sha256"],
                "spec": project,
                "spec_sha256": report["spec_sha256"],
                "build_report_sha256": sha256_file(
                    experiments / BUILD_DIRECTORY / "build-report.json"
                ),
                "total_sample_codes": report["imports"][-1]["allocation"][
                    "total_backing_capacity_codes"
                ],
                "expected_body_sha256": report["target_body_sha256"],
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": report["restore_wav_sha256"],
                "onset_settings": {"kick": ONSET_KICK, "snare": ONSET_SNARE},
                "onset_method_script_sha256": sha256_file(root / "scripts/swing_onset_method.py"),
                "level_settings": LEVEL_SETTINGS,
                "level_method_script_sha256": sha256_file(
                    root / "scripts/polyphony_method_exploratory.py"
                ),
                "expected": EXPECTED,
                "melody_key1_hz": MELODY_KEY1_HZ,
                "tolerances": TOLERANCES,
                "decision": [
                    "The backup must equal the compiled target exactly",
                    "tempo_128: median Sound13 onset interval within 5 ms of 0.469 s",
                    "chain_8: median interval between Sound14 bursts (pairs 8 steps apart, 1.5 s) within 20 ms of the 15.0 s chain cycle",
                    "melody_first_note: the melody's key-1 level in step 1 exceeds step 2 by at least 20 dB",
                ],
                "limits": [
                    "One large project; the spec exercises every slot and pattern once",
                ],
            }
        ),
    )
    print(
        json.dumps(
            {
                "ready": True,
                "folder": DIRECTORY,
                "total_codes": report["imports"][-1]["allocation"]["total_backing_capacity_codes"],
                "restore_wav": report["restore_wav"],
            }
        )
    )


if __name__ == "__main__":
    main()
