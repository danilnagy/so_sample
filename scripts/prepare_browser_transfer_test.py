"""Register the browser-transfer test: the web app's own Send and Import, on the device.

experiments/browser-transfer-001 was built by web/scripts/build-browser-transfer-test.ts
(docs/browser-transfer-control.md): send-project.sosample.zip is the bundled Concrete
project; packets.json is that archive compiled exactly as the app's Send compiles it; and
reference-restore.wav is the same compile as a restore, decoded here into the expected
artifact. It is never played: the browser sends, and `po33 hw run --no-restore` records
and checks the backup.

This script decodes reference-restore.wav with the Python decoder, requires its packets to
equal packets.json, and writes the experiment record and the registration with the
predictions, before any data is taken.
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

DIRECTORY = "browser-transfer-001"
REGISTRATION = "browser-transfer-registration-001.json"
IMPORTED = "imported.sosample.zip"
QUESTIONS = [
    "Send: at what level did the transfer succeed, and how many tries did it take? Did the PO-33 ever show ERR? (notes)",
    "Send: after the transfer, did PLAY on the PO-33 play Concrete (a techno beat with a filtered stab)? (yes/no/notes)",
    "Anything else you noticed (Enter to skip)",
]
INSTRUCTIONS = """# Browser-transfer test, part 1: Send from the app

Do these steps now; the harness records the backup after you press Enter.

1. Start the app from this checkout (`cd web && npm run dev`, then open the address it
   prints in Chrome). The target was compiled by this checkout's code, so use it rather
   than the live site.
2. In the app: Projects, Import project..., choose
   experiments/browser-transfer-001/send-project.sosample.zip. The project "Concrete"
   opens. Do not edit it.
3. Cables: connect the computer's headphone output to the PO-33's input, and unplug the
   PO-33's output from the computer, so the device cannot hear itself.
4. Set the computer's output volume to a fixed, medium level and turn off any sound
   enhancement.
5. On the PO-33, hold write and press sound + record; it waits for the transfer.
6. In the app: Device, Send to PO-33, Play restore, at the default level (60%). It takes
   about 50 s. If the PO-33 shows ERR, try again at another level and note it.
7. When the app says Finished: unplug the computer's output from the PO-33's input, and
   connect the PO-33's output to the computer's stereo line input (the harness's input).

Then press Enter; the harness asks you to start the backup (write + sound + play).
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
    for required in ("reference-restore.wav", "packets.json", "project.json", "send-project.sosample.zip"):
        if not (folder / required).exists():
            raise ValueError(f"Run web/scripts/build-browser-transfer-test.ts first; missing {required}")
    if registration_path.exists() or (folder / "edited.symbols.npz").exists():
        raise ValueError("Fresh registration required")
    packets = load_packets(folder / "packets.json")
    target_path = folder / "edited.symbols.npz"
    subprocess.run(
        [sys.executable, "-m", "po33_re", "decode", str(folder / "reference-restore.wav"), "--out", str(target_path)],
        cwd=root,
        check=True,
        capture_output=True,
    )
    target = decode_artifact(load_artifact(target_path))
    if target.packets != packets or encode_packets(packets) != target.encoded_body:
        target_path.unlink()
        raise ValueError("The decoded reference restore does not carry the TypeScript packets")
    project = json.loads((folder / "project.json").read_text())
    write_bytes(folder / "instructions.md", INSTRUCTIONS.encode())
    write_bytes(
        folder / "experiment.json",
        json_bytes(
            {
                "experiment_id": DIRECTORY,
                "capture_status": "awaiting_hardware_session",
                # The browser sends; this file does not exist, so `hw run` plays no restore.
                "restore_file": "sent-by-the-browser.wav",
                "expected_artifact": "edited.symbols.npz",
                "registration": "../" + REGISTRATION,
                "builder": "web/scripts/build-browser-transfer-test.ts",
                "observation_questions": QUESTIONS,
                "hardware_restore": {"status": "not_run"},
            }
        ),
    )
    write_bytes(
        registration_path,
        json_bytes(
            {
                "analysis_version": "browser-transfer-registration-0.1",
                "hardware_verified": False,
                "registered_before_new_native_captures": True,
                "experiment_id": DIRECTORY,
                "expected_artifact_source": "Python decode of reference-restore.wav, the TypeScript compile of send-project.sosample.zip as the app's Send compiles it",
                "send_project_sha256": sha256_file(folder / "send-project.sosample.zip"),
                "packets_json_sha256": sha256_file(folder / "packets.json"),
                "project_json_sha256": sha256_file(folder / "project.json"),
                "reference_restore_wav_sha256": sha256_file(folder / "reference-restore.wav"),
                "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
                "edited_artifact_sha256": sha256_file(target_path),
                "decoded_reference_carries_typescript_packets": True,
                "project": project,
                "tempo": tempo(target),
                "swing": swing(target),
                "chain": pattern_chain(target),
                "import_check_script": "web/scripts/check-browser-import.ts",
                "import_check_tools_sha256": sha256_file(root / "web/scripts/browser-transfer-tools.ts"),
                "imported_archive": IMPORTED,
                "predictions": {
                    "send": "The backup the device makes after the browser's Send equals the compiled target exactly (every packet and the whole body)",
                    "import": "The project the app makes from its own recording of that backup (Device, Import from PO-33), exported as a project archive, compiles to a state that plays the same as the target: every sound the same codes from the same owner, every pattern byte for byte, the same chain, tempo and swing, and no more pages",
                },
                "decision": [
                    "The send prediction is decided by the native check of the harness's backup against the target",
                    "The import prediction is decided by web/scripts/check-browser-import.ts on the exported archive",
                    "Each is recorded as held or failed independently; a failure is kept with its evidence",
                    "The level that succeeded, retries and ERR are exploratory, from the session answers",
                ],
                "limits": [
                    "One session on one device, with this computer's audio interface and Chrome",
                    "The import is judged after the app's own export, which fits clip windows to their samples as Send does; the browser's decode itself is not compared packet by packet",
                ],
            }
        ),
    )
    print(json.dumps({"ready": True, "folder": DIRECTORY, "packets": len(packets), "pages": project["pages"]}))


if __name__ == "__main__":
    main()
