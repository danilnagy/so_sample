"""Check the browser-transfer test: the browser's Send (exact backup), then its Import."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from po33_re.artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from po33_re.formats.packets import decode_artifact, encode_packets, frame_report
from po33_re.modem.symbols import load_artifact
from scripts.prepare_browser_transfer_test import DIRECTORY, IMPORTED, REGISTRATION

IMPORT_RESULTS = "browser-import-results-001.json"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    registration_path = root / "experiments" / REGISTRATION
    registration = json.loads(registration_path.read_text())
    folder = root / "experiments" / DIRECTORY
    capture = folder / "capture.wav"
    artifact_path = folder / "derived/analysis-001/capture.symbols.npz"
    target_path = folder / "edited.symbols.npz"
    imported = folder / IMPORTED
    native_path = folder / "hardware-recapture-results-001.json"
    import_path = folder / IMPORT_RESULTS
    validate_outputs([native_path, import_path], [capture, artifact_path, target_path, imported], False)
    for name, key in (
        ("edited.symbols.npz", "edited_artifact_sha256"),
        ("packets.json", "packets_json_sha256"),
        ("send-project.sosample.zip", "send_project_sha256"),
    ):
        if sha256_file(folder / name) != registration[key]:
            raise ValueError(f"Registered {name} changed")
    if sha256_file(root / "web/scripts/browser-transfer-tools.ts") != registration["import_check_tools_sha256"]:
        raise ValueError("The registered import check changed")
    artifact = load_artifact(artifact_path)
    capture_hash = sha256_file(capture)
    if artifact.metadata["source_sha256"] != capture_hash:
        raise ValueError("Analysis artifact is not from capture.wav")
    target = decode_artifact(load_artifact(target_path))
    actual = decode_artifact(artifact)
    checks = {
        "native_valid": encode_packets(actual.packets) == actual.encoded_body,
        "target_body_matches_registration": hashlib.sha256(target.encoded_body).hexdigest()
        == registration["expected_body_sha256"],
        "entire_actual_body_and_packets_match_target": actual.packets == target.packets
        and actual.encoded_body == target.encoded_body,
        "capture_is_new": capture_hash != registration["reference_restore_wav_sha256"],
    }
    write_bytes(
        native_path,
        json_bytes(
            {
                "analysis_version": "browser-transfer-native-check-0.1",
                "hardware_verified": False,
                "prediction": "send",
                "passed": all(checks.values()),
                "checks": checks,
                "registration_sha256": sha256_file(registration_path),
                "capture_sha256": capture_hash,
                "artifact_sha256": sha256_file(artifact_path),
                "native_frame": frame_report(actual),
            }
        ),
    )
    # The import is judged whatever the send's result, so both outcomes are kept.
    run = subprocess.run(
        ["npx", "tsx", "scripts/check-browser-import.ts", str(imported), str(folder / "packets.json")],
        cwd=root / "web",
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        raise ValueError(f"The import check could not run: {run.stderr.strip()}")
    result = json.loads(run.stdout.strip().splitlines()[-1])
    write_bytes(
        import_path,
        json_bytes(
            {
                "analysis_version": "browser-transfer-import-check-0.1",
                "hardware_verified": False,
                "prediction": "import",
                "registration_sha256": sha256_file(registration_path),
                "imported_archive_sha256": sha256_file(imported),
                **result,
            }
        ),
    )
    summary = {"send": all(checks.values()), "import": result["passed"], "send_checks": checks, "import_checks": result["checks"]}
    print(json.dumps(summary, indent=2))
    if not (summary["send"] and summary["import"]):
        raise ValueError("A prediction failed; both reports retained")


if __name__ == "__main__":
    main()
