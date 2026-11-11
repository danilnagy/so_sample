"""Register the kit-sharing test: drum sounds referencing another kit's buffer.

The restore in experiments/kit-sharing-001 was built by web/scripts/build-kit-sharing-test.ts
with the compiler's kit sharing on (docs/kit-sharing-control.md): Sound 11 stores a kit of
kick, snare and hat; Sound 12 loads the same kit and references Sound 11's buffer on every
key, storing nothing; Sound 13 stores its own kick and a blip, and references Sound 11's
snare and hat, one of them from part-way into the snare. Six pages instead of ten.

This script decodes the TypeScript restore with the Python decoder into the expected
artifact (as the audition-lock observation did, since the template capture lives on the
research machine) and requires the decoded packets and body to equal the compiler's
packets.json, then writes the experiment record and the registration. Predictions: the backup equals the target exactly; each
pattern plays its kit as the observation questions describe.
"""

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, write_bytes
from po33_re.formats.globals import pattern_chain, swing, tempo
from po33_re.formats.packets import Packet, decode_artifact, encode_packets
from po33_re.modem.symbols import load_artifact

DIRECTORY = "kit-sharing-001"
REGISTRATION = "kit-sharing-registration-001.json"
PLAYBACK_SECONDS = 20
QUESTIONS = [
    "Pattern 1 (Sound 11): did you hear a falling kick on steps 1 and 9, a noise snare on 5 and 13, and short hats on the off-beats? (yes/no/notes)",
    "Pattern 2 (Sound 12): did it sound the same as Pattern 1, every hit present? (yes/no/notes)",
    "Pattern 3 (Sound 13): the same beat, plus a buzzy blip on step 14 and a short snare tail on step 16? (yes/no/notes)",
    "Anything else you noticed (Enter to skip)",
]
INSTRUCTIONS = """# Kit-sharing test

After the restore, press PLAY. The chain plays Patterns 1, 2 and 3 and loops; each is one
bar at 100 BPM, so a pass takes about seven seconds.

- Pattern 1 plays Sound 11: kick on steps 1 and 9, snare on 5 and 13, hat on 3, 7, 11, 15.
- Pattern 2 plays the same beat on Sound 12, whose keys all point into Sound 11's samples.
  It should sound exactly like Pattern 1.
- Pattern 3 plays the same beat on Sound 13, plus a buzzy blip on step 14 and the tail of
  the snare (the snare from part-way in) on step 16.

A silent or wrong hit in Pattern 2 or 3 is the thing to listen for. Let it run for the
playback recording, then answer the questions.
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
                f"Run web/scripts/build-kit-sharing-test.ts first; missing {required}"
            )
    if registration_path.exists() or (folder / "edited.symbols.npz").exists():
        raise ValueError("Fresh registration required")
    packets = load_packets(folder / "packets.json")
    target_path = folder / "edited.symbols.npz"
    subprocess.run(
        [sys.executable, "-m", "po33_re", "decode", str(folder / "restore.wav"), "--out", str(target_path)],
        cwd=root,
        check=True,
        capture_output=True,
    )
    target = decode_artifact(load_artifact(target_path))
    if target.packets != packets or encode_packets(packets) != target.encoded_body:
        target_path.unlink()
        raise ValueError("The decoded restore does not carry the TypeScript packets")
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
                "builder": "web/scripts/build-kit-sharing-test.ts",
                "playback_seconds": PLAYBACK_SECONDS,
                "playback_instructions": INSTRUCTIONS,
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
                "analysis_version": "kit-sharing-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_and_playback_captures": True,
                "experiment_id": DIRECTORY,
                "expected_artifact_source": "Python decode of the TypeScript restore.wav",
                "packets_json_sha256": sha256_file(folder / "packets.json"),
                "project_json_sha256": sha256_file(folder / "project.json"),
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(folder / "edited.symbols.npz"),
                "restore_wav_sha256": sha256_file(folder / "restore.wav"),
                "decoded_restore_carries_typescript_packets": True,
                "tempo": tempo(target),
                "swing": swing(target),
                "chain": pattern_chain(target),
                "sound_data_packets": len(sounds),
                "layout": json.loads((folder / "project.json").read_text())["layout"],
                "predictions": [
                    "The backup equals the compiled target exactly (every packet and the whole body)",
                    "Pattern 2 on Sound 12, whose every key references Sound 11's kit buffer, sounds the same as Pattern 1 on Sound 11",
                    "Pattern 3 on Sound 13 plays its own kick and blip, Sound 11's snare and hat, and a window from 1500 codes into Sound 11's snare on step 16",
                ],
                "decision": [
                    "Exact reception is decided by the native check of the backup against the target",
                    "The audible predictions are decided by the user's answers to the observation questions",
                    "If both hold, the compiler's SHARE_KIT_SAMPLES default is turned on; if either fails, it stays off and the failure is kept",
                ],
                "limits": [
                    "One session on one device; audible predictions rest on listening, not on a frozen measurement",
                    "A drum key referencing another drum sound's kit buffer is tested here for the first time; a melodic owner referenced by drum keys was verified in web-template-001",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "sound_data_packets": len(sounds)}))


if __name__ == "__main__":
    main()
