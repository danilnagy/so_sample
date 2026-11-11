"""Register the web template test: the TypeScript compile step's first restore.

The restore in experiments/web-template-001 was built by web/scripts/build-web-template-test.ts
from the empty-device template (experiments/empty-001-a) and a project that uses every
layout the compiler produces (docs/web-template-control.md): a melodic sample owned by
Sound 1 and referenced by Sounds 2 and 3 with other windows, a drum kit with its own
buffer, a key with no record, a key referencing Sound 1's buffer, a sample shared by
several keys, and a second kit that slices one sample into sixteen overlapping windows.

This script rebuilds the same packets with the Python encoder and requires the two
restore WAVs to be byte-identical, then writes the expected artifact, the experiment
record and the registration. Predictions: the backup equals the target exactly; the
observation questions record what each layout does audibly.
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import Packet, decode_artifact, encode_packets, rebuild_labels
from po33_re.modem.encode import encode_artifact
from po33_re.modem.symbols import load_artifact

DIRECTORY = "web-template-001"
REGISTRATION = "web-template-registration-001.json"
TEMPLATE_ARTIFACT = "experiments/empty-001-a/derived/analysis-001/capture.symbols.npz"
PLAYBACK_SECONDS = 22
QUESTIONS = [
    "Pattern 1: did Sound 2 (steps 3, 11) play the Sound 1 tone but shorter, and Sound 3 (step 7) start part-way into it? (yes/no/notes)",
    "Pattern 1 drums (Sound 9): was key 4 (step 7) silent, and did key 5 (step 11) play the Sound 1 tone? (yes/no/notes)",
    "Pattern 2: did Sound 10 play rising chirp fragments on every step, with FX 1 looping steps 9-12? (yes/no/notes)",
    "Anything else you noticed (Enter to skip)",
]
INSTRUCTIONS = """# Web template test

After the restore, press PLAY. The chain plays Pattern 1 then Pattern 2 and loops.

- Pattern 1: Sound 1 plays a tone on steps 1, 5, 9, 13 (step 9 darker: filter lock), a
  volume lock on step 2 without a note, Sound 2 a shorter copy of the tone on 3 and 11,
  Sound 3 the tone from part-way in on step 7. Drums (Sound 9): kick 1, 9; snare 5, 13;
  kick tail 3; key 4 on step 7 has no sample and should be silent; key 5 on step 11 is
  the Sound 1 tone; key 6 on step 15 is the snare again.
- Pattern 2: Sound 10 plays sixteen slices of a rising chirp, one per step; FX 1 is held
  on steps 9 to 12.

Let it run for the playback recording, then answer the questions.
"""


def load_packets(path):
    view = json.loads(path.read_text())
    if view.get("schema") != "sosample.packets":
        raise ValueError("Expected a sosample packets file")
    return tuple(Packet(p["tag"], base64.b64decode(p["payload"])) for p in view["packets"])


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments" / DIRECTORY
    registration_path = root / "experiments" / REGISTRATION
    for required in ("restore.wav", "packets.json", "project.json"):
        if not (folder / required).exists():
            raise ValueError(
                f"Run web/scripts/build-web-template-test.ts first; missing {required}"
            )
    if registration_path.exists() or (folder / "edited.symbols.npz").exists():
        raise ValueError("Fresh registration required")
    packets = load_packets(folder / "packets.json")
    source = load_artifact(root / TEMPLATE_ARTIFACT)
    edited = rebuild_labels(source, packets)
    edited.metadata["transformations"].append(
        {
            "kind": "sosample-typescript-compile",
            "template_capture_sha256": source.metadata["source_sha256"],
            "packets_json_sha256": sha256_file(folder / "packets.json"),
            "project_json_sha256": sha256_file(folder / "project.json"),
            "hardware_verified": False,
        }
    )
    target = decode_artifact(edited)
    if target.packets != packets or encode_packets(packets) != target.encoded_body:
        raise ValueError("Rebuilt labels do not carry the TypeScript packets")
    waveform, _ = encode_artifact(edited)
    ts_wav = (folder / "restore.wav").read_bytes()
    if waveform != ts_wav:
        raise ValueError("The TypeScript restore is not byte-identical to the Python encoder's")
    write_bytes(folder / "edited.symbols.npz", edited.to_bytes())
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                "restore_file": "restore.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "builder": "web/scripts/build-web-template-test.ts",
                "playback_seconds": PLAYBACK_SECONDS,
                "observation_questions": QUESTIONS,
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    sounds = {
        i: (len(p.payload), p.payload[:9].hex()) for i, p in enumerate(packets) if p.tag == 0xEF78
    }
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "web-template-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "template_artifact": TEMPLATE_ARTIFACT,
                "template_capture_sha256": source.metadata["source_sha256"],
                "packets_json_sha256": sha256_file(folder / "packets.json"),
                "project_json_sha256": sha256_file(folder / "project.json"),
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "typescript_and_python_restores_identical": True,
                "tempo": tempo(target),
                "swing": swing(target),
                "chain": pattern_chain(target),
                "sound_data_packets": len(sounds),
                "predictions": [
                    "The backup equals the compiled target exactly (every packet and the whole body)",
                    "Sound 2 plays the Sound 1 tone truncated at 5000 codes; Sound 3 plays it from code 3000 to 9000",
                    "Sound 9 key 4, which has no record, is silent; key 5 plays Sound 1's buffer window 0..4000",
                    "Sound 10's sixteen windows into one buffer each play, including the overlapping key 2",
                ],
                "decision": [
                    "Exact reception is decided by the native check of the backup against the target",
                    "The audible predictions are decided by the user's answers to the observation questions",
                ],
                "limits": [
                    "One session on one device; audible predictions rest on listening, not on a frozen measurement",
                    "An empty key as an absent record is tested here for the first time",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "sound_data_packets": len(sounds)}))


if __name__ == "__main__":
    main()
