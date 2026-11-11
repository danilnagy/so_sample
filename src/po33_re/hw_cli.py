"""Command-line entry points for hardware sessions and research batches."""

import json
import sys
from pathlib import Path

from .artifacts import json_bytes
from .hardware.audio_io import SounddeviceBackend, list_devices, play_wav
from .hardware.session import (
    CONFIG_NAME,
    ConsoleUI,
    HardwareConfig,
    SessionOptions,
    loopback_check,
    reanalyze_session,
    run_playback_session,
    run_session,
)
from .hardware.verify import ESTABLISHED_THRESHOLD
from .research_batch import build_batch


def add_commands(commands):
    hw = commands.add_parser("hw", help="Guided hardware round trips through an audio interface")
    sub = hw.add_subparsers(dest="hw_command", required=True)

    def device_options(p):
        p.add_argument("--config", type=Path, default=Path(CONFIG_NAME))
        p.add_argument("--input", help="Input device index or name fragment")
        p.add_argument("--output", help="Output device index or name fragment")
        p.add_argument("--hostapi", help="Host API name fragment, e.g. MME or WASAPI")

    devices = sub.add_parser("devices", help="List audio devices")
    devices.add_argument("--json", action="store_true")
    config = sub.add_parser("config", help="Save the audio devices and recording format")
    device_options(config)
    config.add_argument("--rate", type=int, choices=(44100, 48000))
    config.add_argument("--subtype", choices=("PCM_16", "PCM_24"))
    config.add_argument("--playback-gain", type=float, help="Restore playback gain 0..1")
    config.add_argument(
        "--input-cable",
        choices=("unplug", "keep"),
        help="Prompt for cable swaps around each restore (default unplug)",
    )
    run = sub.add_parser("run", help="Restore, back up, check, record playback and ask questions")
    device_options(run)
    run.add_argument("folder", type=Path)
    run.add_argument("--new", action="store_true", help="Create the folder (observation runs)")
    run.add_argument("--no-restore", action="store_true", help="Skip the restore step")
    run.add_argument("--expect", type=Path, help="Expected native target artifact")
    run.add_argument("--baseline", type=Path, help="Artifact to describe changes against")
    run.add_argument("--playback", type=float, help="Seconds of playback to record")
    run.add_argument("--no-playback", action="store_true")
    run.add_argument("--max-attempts", type=int, default=5)
    run.add_argument("--threshold", type=float, default=ESTABLISHED_THRESHOLD)
    run.add_argument("--no-questions", action="store_true")
    run.add_argument(
        "--retry",
        action="store_true",
        help="Run a folder again: archive the previous session's accepted copies first",
    )
    reanalyze = sub.add_parser(
        "reanalyze", help="Re-decode a session's kept backups with the current analysis"
    )
    reanalyze.add_argument("folder", type=Path)
    reanalyze.add_argument("--threshold", type=float, default=ESTABLISHED_THRESHOLD)
    playback = sub.add_parser("playback", help="Record only ordinary playback into a folder")
    device_options(playback)
    playback.add_argument("folder", type=Path)
    playback.add_argument("--seconds", type=float, required=True)
    playback.add_argument("--max-attempts", type=int, default=5)
    play = sub.add_parser("play", help="Play one WAV to the PO-33 input (no backup)")
    device_options(play)
    play.add_argument("wav", type=Path)
    play.add_argument("--gain", type=float, help="Software gain 0..1 (default: configured)")
    loop = sub.add_parser("loopback", help="Check the playback path with a patch cable, no device")
    device_options(loop)
    loop.add_argument("restore_wav", type=Path)
    loop.add_argument("--expect", type=Path, required=True)
    loop.add_argument("--out-dir", type=Path, required=True)

    batch = commands.add_parser("build-batch", help="Build one research restore from raw edits")
    batch.add_argument("spec", type=Path)
    batch.add_argument("--out-dir", type=Path, required=True)


def _config(args):
    config = HardwareConfig.load(args.config)
    for name, attribute in (("input", "input_device"), ("output", "output_device")):
        if getattr(args, name, None) is not None:
            setattr(config, attribute, getattr(args, name))
    if getattr(args, "hostapi", None) is not None:
        config.hostapi = args.hostapi
    return config


def _backend(config):
    return SounddeviceBackend(config.input_device, config.output_device, config.hostapi)


def run_command(args, backend_factory=_backend, ui=None):
    ui = ui or ConsoleUI()
    if args.command == "build-batch":
        report = build_batch(args.spec, args.out_dir)
        expected = report["expected_changes_from_source"]
        sys.stdout.write(
            json_bytes(
                {
                    "restore_file": str(args.out_dir / "restore.wav"),
                    "passed": report["passed"],
                    "target_body_sha256": report["target_body_sha256"],
                    "expected_change_count": expected["change_count"],
                    "no_op_operations": report["no_op_operations"],
                    "hardware_verified": False,
                }
            ).decode("utf-8")
        )
        return 0
    if args.hw_command == "devices":
        devices = list_devices()
        if args.json:
            sys.stdout.write(json.dumps(devices, indent=2) + "\n")
            return 0
        for d in devices:
            marks = ("in " if d["default_input"] else "") + ("out" if d["default_output"] else "")
            print(
                f"{d['index']:3d}  {d['name'][:48]:48s} {d['hostapi']:20s} "
                f"in {d['max_input_channels']} out {d['max_output_channels']}  {marks}"
            )
        return 0
    if args.hw_command == "reanalyze":
        record = reanalyze_session(args.folder, ui, args.threshold)
        result = record["result"]
        if not result["backup_decoded"] or result["native_target_exact"] is False:
            return 3
        return 0
    config = _config(args)
    if args.hw_command == "config":
        if args.rate:
            config.sample_rate = args.rate
        if args.subtype:
            config.subtype = args.subtype
        if args.input_cable:
            config.input_cable = args.input_cable
        if args.playback_gain is not None:
            config.playback_gain = args.playback_gain
        backend = backend_factory(config)
        config.save(args.config)
        sys.stdout.write(json_bytes({"config": str(args.config), **backend.describe()}).decode())
        return 0
    backend = backend_factory(config)
    if args.hw_command == "playback":
        record = run_playback_session(
            args.folder, backend, ui, config, args.seconds, args.max_attempts
        )
        playback = record["playback"]
        if not playback["file"] or playback.get("accepted_with_findings"):
            return 3
        return 0
    if args.hw_command == "play":
        gain = config.playback_gain if args.gain is None else args.gain
        ui.say(f"Playing {args.wav} at gain {gain:g}. Press Enter to start.")
        ui.ask("Enter:")
        report = play_wav(backend, args.wav, gain)
        ui.say(
            f"Finished: {report['duration_seconds']:.1f} s, peak {report['peak_after_gain']:.3f}"
        )
        if report["stream_status_flags"]:
            ui.say(f"Driver reported: {report['stream_status_flags']}")
        return 0
    if args.hw_command == "loopback":
        report = loopback_check(backend, args.restore_wav, args.expect, args.out_dir, config)
        verdict = report.get("exact_target_body")
        print(
            "Loopback recovered the exact target body"
            if verdict
            else "Loopback did NOT recover the exact target; see loopback-report.json"
        )
        return 0 if verdict else 3
    if args.new:
        args.folder.mkdir(parents=False, exist_ok=True)  # run_session refuses existing captures
    options = SessionOptions(
        restore=False if args.no_restore else None,
        expected=args.expect,
        baseline=args.baseline,
        playback_seconds=0 if args.no_playback else args.playback,
        questions=[] if args.no_questions else None,
        max_attempts=args.max_attempts,
        threshold=args.threshold,
        retry=args.retry,
    )
    record = run_session(args.folder, backend, ui, config, options)
    result = record["result"]
    if not result["backup_decoded"] or result["native_target_exact"] is False:
        return 3
    return 0
