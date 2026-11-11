import argparse
import hashlib
import sys
from pathlib import Path

from . import __version__
from .analysis.coding import coding_report
from .analysis.diff import compare_bytes
from .artifacts import json_bytes, sha256_file, validate_outputs, write_bytes
from .audio import inspect_wav
from .edits import compile_edit_plan
from .formats.drums import (
    DRUM_SLICE_CALIBRATIONS,
    calibrated_drum_slice,
    replace_calibrated_drum_slice_end,
)
from .formats.packets import (
    calibrated_nonzero_reference,
    decode_artifact,
    encode_packets,
    frame_report,
    rebuild_labels,
    replace_calibrated_reference_end,
    replace_calibrated_reference_window,
)
from .formats.patterns import (
    clone_sound_cell,
    clone_step,
    patterns_report,
    remove_sound_cell,
    set_melodic_key,
)
from .hardware.audio_io import HardwareUnavailable
from .hw_cli import add_commands as add_hardware_commands
from .hw_cli import run_command as run_hardware_command
from .modem.clock_decode import decode_clock_wav
from .modem.decode import DEFAULT_THRESHOLD, DecodeFailure, decode_wav
from .modem.encode import DEFAULT_ENCODER_CARRIER_HZ, encode_file
from .modem.roundtrip import run_roundtrip
from .modem.symbols import load_artifact, pack_symbols
from .project import export_project
from .sample_import import compile_sample_import


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Experimental PO-33 backup research tools")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    sample = commands.add_parser(
        "import-sample", help="Import a PCM WAV into an empty or unshared Sound6 or Sound7"
    )
    sample.add_argument("artifact", type=Path)
    sample.add_argument("sample_wav", type=Path)
    sample.add_argument("--sound", type=int, required=True)
    sample.add_argument("--channel", choices=("left", "right", "mix"))
    sample.add_argument("--capacity", type=int, choices=(4096, 32768, 36864))
    sample.add_argument("--out-dir", type=Path, required=True)
    edits = commands.add_parser(
        "apply-edits", help="Compile a hash-bound plan of supported edits to restore audio"
    )
    edits.add_argument("artifact", type=Path)
    edits.add_argument("--plan", type=Path, required=True)
    edits.add_argument("--out-dir", type=Path, required=True)
    project = commands.add_parser(
        "export-project", help="Export read-only sample/pattern views and exact source packets"
    )
    project.add_argument("artifact", type=Path)
    project.add_argument("--capture", type=Path, required=True)
    project.add_argument("--out-dir", type=Path, required=True)
    project.add_argument(
        "--calibrated-windows",
        action="store_true",
        help="Include Sound3 previews at the two observed start positions",
    )
    project.add_argument(
        "--calibrated-drum-slices",
        action="store_true",
        help="Include calibrated Sound9/keys1 and2 and accepted copied Sound10/key1 previews",
    )
    endpoint = commands.add_parser(
        "set-sound-end", help="Experimentally set endpoint at either calibrated Sound3 start"
    )
    endpoint.add_argument("artifact", type=Path)
    endpoint.add_argument("--sound", type=int, required=True)
    endpoint.add_argument("--end", type=int, required=True)
    endpoint.add_argument("--out", type=Path, required=True)
    endpoint.add_argument("--report", type=Path)
    endpoint.add_argument("--force", action="store_true")
    window = commands.add_parser(
        "set-sound-window", help="Set a Sound3 window at one of the two observed starts"
    )
    window.add_argument("artifact", type=Path)
    window.add_argument("--sound", type=int, required=True)
    window.add_argument("--start", type=int, required=True)
    window.add_argument("--end", type=int, required=True)
    window.add_argument("--out", type=Path, required=True)
    window.add_argument("--report", type=Path)
    window.add_argument("--force", action="store_true")
    drum = commands.add_parser(
        "set-drum-slice-end",
        help="Experimentally set Sound9/key1 or2 endpoint in its local interval",
    )
    drum.add_argument("artifact", type=Path)
    drum.add_argument("--sound", type=int, required=True)
    drum.add_argument("--slice", type=int, required=True)
    drum.add_argument("--end", type=int, required=True)
    drum.add_argument("--out", type=Path, required=True)
    drum.add_argument("--report", type=Path)
    drum.add_argument("--force", action="store_true")
    inspect = commands.add_parser("inspect", help="Inspect stereo PCM WAV without changing it")
    inspect.add_argument("capture", type=Path)
    inspect.add_argument("--json", type=Path)
    inspect.add_argument("--force", action="store_true")
    compare = commands.add_parser("compare", help="Compare binary files at strict offsets")
    compare.add_argument("a", type=Path)
    compare.add_argument("b", type=Path)
    compare.add_argument("--json", type=Path)
    compare.add_argument("--xor", type=Path)
    compare.add_argument("--force", action="store_true")
    decode = commands.add_parser(
        "decode", help="Experimental independent channel phase demodulation"
    )
    decode.add_argument("capture", type=Path)
    decode.add_argument("--out", type=Path, required=True)
    decode.add_argument("--report", type=Path)
    decode.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    decode.add_argument("--force", action="store_true")
    clock = commands.add_parser("decode-clock", help="Experimental measured-clock packet recovery")
    clock.add_argument("capture", type=Path)
    clock.add_argument("--acquisition", type=Path, required=True)
    clock.add_argument("--out", type=Path, required=True)
    clock.add_argument("--report", type=Path)
    clock.add_argument("--force", action="store_true")
    export = commands.add_parser("export-symbols", help="Pack one channel with a count sidecar")
    export.add_argument("artifact", type=Path)
    export.add_argument("--channel", choices=("left", "right"), required=True)
    export.add_argument("--out", type=Path, required=True)
    export.add_argument("--force", action="store_true")
    encode = commands.add_parser("encode", help="Experimental phase waveform reconstruction")
    encode.add_argument("artifact", type=Path)
    encode.add_argument("--out", type=Path, required=True)
    encode.add_argument("--report", type=Path)
    encode.add_argument("--sample-rate", type=int, choices=(44100, 48000), default=44100)
    encode.add_argument("--amplitude", type=float, default=0.5)
    encode.add_argument("--carrier-hz", type=float, default=DEFAULT_ENCODER_CARRIER_HZ)
    encode.add_argument("--force", action="store_true")
    roundtrip = commands.add_parser("roundtrip", help="Strict software decode/encode/decode check")
    roundtrip.add_argument("capture", type=Path)
    roundtrip.add_argument("--out-dir", type=Path, required=True)
    roundtrip.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    roundtrip.add_argument("--sample-rate", type=int, choices=(44100, 48000), default=44100)
    roundtrip.add_argument("--amplitude", type=float, default=0.5)
    roundtrip.add_argument("--carrier-hz", type=float, default=DEFAULT_ENCODER_CARRIER_HZ)
    roundtrip.add_argument("--force", action="store_true")
    coding = commands.add_parser(
        "analyze-coding", help="Bounded research probes; no payload decoding"
    )
    coding.add_argument("baseline", type=Path)
    coding.add_argument("variants", type=Path, nargs="+")
    coding.add_argument("--out", type=Path, required=True)
    coding.add_argument("--window-start", type=int, default=20000)
    coding.add_argument("--force", action="store_true")
    coding.add_argument(
        "--audio-captures",
        type=Path,
        nargs="+",
        help="Optional WAVs in baseline/variant order for clock probes",
    )
    packets = commands.add_parser("decode-packets", help="Read checksum-validated PO-33 packets")
    packets.add_argument("artifact", type=Path)
    packets.add_argument("--out", type=Path, required=True)
    packets.add_argument("--body-out", type=Path)
    packets.add_argument("--force", action="store_true")
    patterns = commands.add_parser("inspect-patterns", help="Inspect raw observed pattern regions")
    patterns.add_argument("artifact", type=Path)
    patterns.add_argument("--out", type=Path, required=True)
    patterns.add_argument("--force", action="store_true")
    clone = commands.add_parser(
        "clone-step", help="Experimentally copy one opaque event to empty steps"
    )
    clone.add_argument("artifact", type=Path)
    clone.add_argument("--pattern", type=int, required=True)
    clone.add_argument("--source-step", type=int, required=True)
    clone.add_argument("--target-steps", type=int, nargs="+", required=True)
    clone.add_argument("--out", type=Path, required=True)
    clone.add_argument("--report", type=Path)
    clone.add_argument("--force", action="store_true")
    cell = commands.add_parser(
        "clone-sound-cell", help="Experimentally copy the observed Sound2 key1 cell"
    )
    cell.add_argument("artifact", type=Path)
    cell.add_argument("--pattern", type=int, required=True)
    cell.add_argument("--sound", type=int, required=True)
    cell.add_argument("--source-step", type=int, required=True)
    cell.add_argument("--target-steps", type=int, nargs="+", required=True)
    cell.add_argument("--out", type=Path, required=True)
    cell.add_argument("--report", type=Path)
    cell.add_argument("--force", action="store_true")
    remove = commands.add_parser(
        "remove-sound-cell", help="Experimentally remove observed Sound2 key1 cells"
    )
    remove.add_argument("artifact", type=Path)
    remove.add_argument("--pattern", type=int, required=True)
    remove.add_argument("--sound", type=int, required=True)
    remove.add_argument("--steps", type=int, nargs="+", required=True)
    remove.add_argument("--out", type=Path, required=True)
    remove.add_argument("--report", type=Path)
    remove.add_argument("--force", action="store_true")
    key = commands.add_parser(
        "set-note-key", help="Experimentally set calibrated Sound3 key1/2/7/16"
    )
    key.add_argument("artifact", type=Path)
    key.add_argument("--pattern", type=int, required=True)
    key.add_argument("--step", type=int, required=True)
    key.add_argument("--sound", type=int, required=True)
    key.add_argument("--key", type=int, required=True)
    key.add_argument("--out", type=Path, required=True)
    key.add_argument("--report", type=Path)
    key.add_argument("--force", action="store_true")
    add_hardware_commands(commands)
    return root


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    try:
        if args.command in ("hw", "build-batch"):
            return run_hardware_command(args)
        if args.command == "import-sample":
            report = compile_sample_import(
                args.artifact,
                args.sample_wav,
                args.out_dir,
                args.sound,
                args.channel,
                args.capacity,
            )
            sys.stdout.write(
                json_bytes(
                    {
                        "restore_file": str(args.out_dir / "restore.wav"),
                        "report_file": str(args.out_dir / "import-report.json"),
                        "passed": report["passed"],
                        "target_body_sha256": report["target_body_sha256"],
                        "allocation": report["allocation"],
                        "hardware_verified": False,
                    }
                ).decode("utf-8")
            )
            return 0
        if args.command == "apply-edits":
            report = compile_edit_plan(args.artifact, args.plan, args.out_dir)
            sys.stdout.write(
                json_bytes(
                    {
                        "restore_file": str(args.out_dir / "restore.wav"),
                        "report_file": str(args.out_dir / "compile-report.json"),
                        "passed": report["passed"],
                        "target_body_sha256": report["target_body_sha256"],
                        "hardware_verified": False,
                    }
                ).decode("utf-8")
            )
            return 0
        if args.command == "export-project":
            report = export_project(
                args.artifact,
                args.capture,
                args.out_dir,
                args.calibrated_windows,
                args.calibrated_drum_slices,
            )
            sys.stdout.write(
                json_bytes(
                    {
                        "project_file": str(args.out_dir / "project.json"),
                        "report_file": str(args.out_dir / "export-report.json"),
                        "pattern_count": report["pattern_count"],
                        "preview_sound_slots": report["preview_sound_slots"],
                        "preview_drum_slices": report["preview_drum_slices"],
                        "native_body_sha256": report["native_body_sha256"],
                        "read_only": True,
                    }
                ).decode("utf-8")
            )
            return 0
        if args.command == "set-drum-slice-end":
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.artifact], args.force)
            source = load_artifact(args.artifact)
            frame = decode_artifact(source)
            _, start, _, _ = calibrated_drum_slice(frame, args.sound, args.slice)
            artifact = rebuild_labels(
                source, replace_calibrated_drum_slice_end(frame, args.sound, args.slice, args.end)
            )
            operation = {
                "kind": "calibrated-drum-slice-end-edit",
                "sound_slot": args.sound,
                "slice_key": args.slice,
                "selector_id": DRUM_SLICE_CALIBRATIONS[args.slice][0],
                "start_field": start,
                "endpoint_field": args.end,
                "source_artifact_sha256": sha256_file(args.artifact),
                "hardware_verified": False,
            }
            artifact.metadata["transformations"].append(operation)
            write_bytes(args.out, artifact.to_bytes(), args.force)
            if args.report:
                write_bytes(
                    args.report,
                    json_bytes(
                        {**operation, "native_frame": frame_report(decode_artifact(artifact))}
                    ),
                    args.force,
                )
            return 0
        if args.command in ("set-sound-end", "set-sound-window"):
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.artifact], args.force)
            source = load_artifact(args.artifact)
            frame = decode_artifact(source)
            if args.command == "set-sound-window":
                start = args.start
                packets = replace_calibrated_reference_window(frame, args.sound, start, args.end)
            else:
                _, start, _, _ = calibrated_nonzero_reference(frame, args.sound)
                packets = replace_calibrated_reference_end(frame, args.sound, args.end)
            artifact = rebuild_labels(source, packets)
            operation = {
                "kind": (
                    "calibrated-nonzero-reference-window-edit"
                    if args.command == "set-sound-window"
                    else "calibrated-nonzero-reference-end-edit"
                ),
                "sound_slot": args.sound,
                "start_field": start,
                "endpoint_field": args.end,
                "source_artifact_sha256": sha256_file(args.artifact),
                "hardware_verified": False,
            }
            artifact.metadata["transformations"].append(operation)
            write_bytes(args.out, artifact.to_bytes(), args.force)
            if args.report:
                write_bytes(
                    args.report,
                    json_bytes(
                        {**operation, "native_frame": frame_report(decode_artifact(artifact))}
                    ),
                    args.force,
                )
            return 0
        if args.command == "decode-clock":
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.capture, args.acquisition], args.force)
            artifact, report = decode_clock_wav(args.capture, load_artifact(args.acquisition))
            write_bytes(args.out, artifact.to_bytes(), args.force)
            if args.report:
                write_bytes(args.report, json_bytes(report), args.force)
            return 0
        if args.command == "set-note-key":
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.artifact], args.force)
            source = load_artifact(args.artifact)
            frame = decode_artifact(source)
            packets = set_melodic_key(frame, args.pattern, args.step, args.sound, args.key)
            artifact = rebuild_labels(source, packets)
            operation = {
                "kind": "calibrated-melodic-key-edit",
                "pattern_slot": args.pattern,
                "step": args.step,
                "sound_slot": args.sound,
                "keyboard_key": args.key,
                "source_artifact_sha256": sha256_file(args.artifact),
                "hardware_verified": False,
            }
            artifact.metadata["transformations"].append(operation)
            report = {**operation, "native_frame": frame_report(decode_artifact(artifact))}
            write_bytes(args.out, artifact.to_bytes(), args.force)
            if args.report:
                write_bytes(args.report, json_bytes(report), args.force)
            return 0
        if args.command == "remove-sound-cell":
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.artifact], args.force)
            source = load_artifact(args.artifact)
            packets = remove_sound_cell(
                decode_artifact(source), args.pattern, args.sound, args.steps
            )
            artifact = rebuild_labels(source, packets)
            operation = {
                "kind": "observed-sound-cell-removal",
                "pattern_slot": args.pattern,
                "sound_slot": args.sound,
                "steps": args.steps,
                "source_artifact_sha256": sha256_file(args.artifact),
                "hardware_verified": False,
            }
            artifact.metadata["transformations"].append(operation)
            report = {**operation, "native_frame": frame_report(decode_artifact(artifact))}
            write_bytes(args.out, artifact.to_bytes(), args.force)
            if args.report:
                write_bytes(args.report, json_bytes(report), args.force)
            return 0
        if args.command in {"clone-step", "clone-sound-cell"}:
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.artifact], args.force)
            source = load_artifact(args.artifact)
            frame = decode_artifact(source)
            if args.command == "clone-sound-cell":
                packets = clone_sound_cell(
                    frame, args.pattern, args.sound, args.source_step, args.target_steps
                )
            else:
                packets = clone_step(frame, args.pattern, args.source_step, args.target_steps)
            artifact = rebuild_labels(source, packets)
            operation = {
                "kind": "opaque-sound-cell-clone"
                if args.command == "clone-sound-cell"
                else "opaque-step-clone",
                "pattern_slot": args.pattern,
                "source_step": args.source_step,
                "target_steps": args.target_steps,
                "source_artifact_sha256": sha256_file(args.artifact),
                "hardware_verified": False,
            }
            if args.command == "clone-sound-cell":
                operation["sound_slot"] = args.sound
            artifact.metadata["transformations"].append(operation)
            report = {**operation, "native_frame": frame_report(decode_artifact(artifact))}
            write_bytes(args.out, artifact.to_bytes(), args.force)
            if args.report:
                write_bytes(args.report, json_bytes(report), args.force)
            return 0
        if args.command == "inspect-patterns":
            validate_outputs([args.out], [args.artifact], args.force)
            artifact = load_artifact(args.artifact)
            report = patterns_report(decode_artifact(artifact))
            report.update(
                source_sha256=artifact.metadata["source_sha256"],
                artifact_sha256=sha256_file(args.artifact),
            )
            write_bytes(args.out, json_bytes(report), args.force)
            return 0
        if args.command == "decode-packets":
            outputs = [args.out] + ([args.body_out] if args.body_out else [])
            validate_outputs(outputs, [args.artifact], args.force)
            artifact = load_artifact(args.artifact)
            frame = decode_artifact(artifact)
            if encode_packets(frame.packets) != frame.encoded_body:
                raise ValueError("Packet re-encoding differs from captured body")
            report = frame_report(frame)
            report.update(
                source_sha256=artifact.metadata["source_sha256"],
                artifact_sha256=sha256_file(args.artifact),
                exact_body_reencode=True,
            )
            if args.body_out:
                write_bytes(args.body_out, frame.encoded_body, args.force)
            write_bytes(args.out, json_bytes(report), args.force)
            return 0
        if args.command == "analyze-coding":
            validate_outputs(
                [args.out],
                [args.baseline, *args.variants, *(args.audio_captures or [])],
                args.force,
            )
            report = coding_report(
                args.baseline, args.variants, args.window_start, args.audio_captures
            )
            write_bytes(args.out, json_bytes(report), args.force)
            print(
                "warning: Coding probes do not decode payload or confirm state fields.",
                file=sys.stderr,
            )
            return 0
        if args.command in {"inspect", "compare"}:
            inputs = [args.capture] if args.command == "inspect" else [args.a, args.b]
            outputs = [p for p in (args.json, getattr(args, "xor", None)) if p is not None]
            validate_outputs(outputs, inputs, args.force)
            if args.command == "inspect":
                report = inspect_wav(args.capture)
            else:
                a, b = args.a.read_bytes(), args.b.read_bytes()
                report = compare_bytes(a, b)
                report.update(
                    {
                        "schema_version": 1,
                        "path_a": str(args.a),
                        "path_b": str(args.b),
                        "sha256_a": sha256_file(args.a),
                        "sha256_b": sha256_file(args.b),
                        "range_convention": "zero-based, end-exclusive",
                    }
                )
        elif args.command == "decode":
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.capture], args.force)
            artifact = decode_wav(args.capture, args.threshold)
            encoded_artifact = artifact.to_bytes()
            report = {
                **artifact.metadata,
                "artifact_sha256": hashlib.sha256(encoded_artifact).hexdigest(),
            }
            write_bytes(args.out, encoded_artifact, args.force)
            if args.report:
                write_bytes(args.report, json_bytes(report), args.force)
            else:
                sys.stdout.write(json_bytes(report).decode("utf-8"))
            for warning in artifact.metadata["warnings"]:
                print(f"warning: {warning}", file=sys.stderr)
            return 0
        elif args.command == "encode":
            outputs = [args.out] + ([args.report] if args.report else [])
            validate_outputs(outputs, [args.artifact], args.force)
            waveform, report = encode_file(
                args.artifact, args.sample_rate, args.amplitude, args.carrier_hz
            )
            report["output_sha256"] = hashlib.sha256(waveform).hexdigest()
            write_bytes(args.out, waveform, args.force)
            if args.report:
                write_bytes(args.report, json_bytes(report), args.force)
            else:
                sys.stdout.write(json_bytes(report).decode("utf-8"))
            print(
                "warning: Experimental waveform; hardware acceptance is not verified.",
                file=sys.stderr,
            )
            return 0
        elif args.command == "roundtrip":
            report = run_roundtrip(
                args.capture,
                args.out_dir,
                args.threshold,
                args.sample_rate,
                args.amplitude,
                args.force,
                args.carrier_hz,
            )
            sys.stdout.write(json_bytes(report).decode("utf-8"))
            print(
                "warning: Software roundtrip does not verify hardware restoration.", file=sys.stderr
            )
            return 0 if report["passed"] else 3
        else:
            sidecar = Path(str(args.out) + ".json")
            validate_outputs([args.out, sidecar], [args.artifact], args.force)
            artifact = load_artifact(args.artifact)
            symbols = getattr(artifact, args.channel + "_symbols")
            packed, report = pack_symbols(symbols)
            report.update(
                {
                    "schema": "po33.packed-phase-symbols",
                    "schema_version": 1,
                    "channel": args.channel,
                    "phase_convention": artifact.metadata["phase_convention"],
                    "source_artifact_sha256": sha256_file(args.artifact),
                    "source_capture_sha256": artifact.metadata["source_sha256"],
                    "packed_sha256": hashlib.sha256(packed).hexdigest(),
                }
            )
            write_bytes(args.out, packed, args.force)
            write_bytes(sidecar, json_bytes(report), args.force)
            return 0
        encoded = json_bytes(report)
        if args.json:
            write_bytes(args.json, encoded, args.force)
        else:
            sys.stdout.write(encoded.decode("utf-8"))
        if getattr(args, "xor", None):
            write_bytes(args.xor, bytes(x ^ y for x, y in zip(a, b)), args.force)
        return 0
    except HardwareUnavailable as exc:
        print(f"hardware unavailable: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted; recordings and the session record are kept", file=sys.stderr)
        return 130
    except DecodeFailure as exc:
        print(f"decode failed: {exc}", file=sys.stderr)
        return 3
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 -- CLI boundary maps unexpected failures to exit 3.
        print(f"processing failed: {exc}", file=sys.stderr)
        return 3
