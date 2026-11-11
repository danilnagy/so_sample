"""Guided hardware session: restore, backup, immediate check, playback, observations.

One command walks through a whole round trip. The person presses the device
buttons; the session plays and records, decodes each backup at once, keeps every
attempt, and writes one session record that separates software checks from what
the person reports. It never edits experiment registrations or prior evidence.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from ..artifacts import json_bytes, sha256_file, write_bytes
from ..formats.packets import decode_artifact
from ..modem.symbols import load_artifact
from .audio_io import (
    PLAYBACK_SIGNAL_PEAK,
    play_wav,
    playback_findings,
    record_fixed,
    record_transfer,
)
from .changes import describe_changes, summarize_change
from .verify import ESTABLISHED_THRESHOLD, analyze_capture, compare_with_target

CONFIG_NAME = ".po33-hardware.json"
SESSION_SCHEMA = "po33.hardware-session"
DEFAULT_QUESTIONS = ("Anything unexpected on the device or in the sound? (Enter to skip)",)
RECEIVE_BUTTONS = "WRITE + SOUND + RECORD"
SEND_BUTTONS = "WRITE + SOUND + PLAY"
MAX_LISTED_CHANGES = 20


@dataclass
class HardwareConfig:
    input_device: str | None = None
    output_device: str | None = None
    hostapi: str | None = None
    sample_rate: int = 44100
    subtype: str = "PCM_16"
    # The PO-33 mixes its line input into its output, so with both cables connected a
    # delayed copy of the signal loops back. "unplug" asks for the cable swaps around
    # the restore; "keep" gives no prompts, for setups without that loop.
    input_cable: str = "unplug"
    # Software gain for restore playback, applied on top of the operating-system volume.
    playback_gain: float = 1.0

    @classmethod
    def load(cls, path):
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        unknown = set(data) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"Unknown hardware config keys: {sorted(unknown)}")
        config = cls(**data)
        if config.input_cable not in ("unplug", "keep"):
            raise ValueError("input_cable must be 'unplug' or 'keep'")
        if not 0 < float(config.playback_gain) <= 1:
            raise ValueError("playback_gain must be in (0, 1]")
        return config

    def save(self, path):
        write_bytes(path, json_bytes(asdict(self)), force=True)


@dataclass
class SessionOptions:
    restore: bool | None = None
    expected: Path | None = None
    baseline: Path | None = None
    playback_seconds: float | None = None
    questions: list | None = None
    max_attempts: int = 5
    threshold: float = ESTABLISHED_THRESHOLD
    max_wait_seconds: float = 120.0
    retry: bool = False
    extra: dict = field(default_factory=dict)


class ConsoleUI:
    def say(self, text=""):
        print(text, flush=True)

    def ask(self, text):
        return input(f"{text} ").strip()

    def progress(self, info):
        state = "signal" if info.get("signal") else "waiting"
        print(f"\r  recording {info['seconds']:6.1f} s  [{state}]   ", end="", flush=True)

    def end_progress(self):
        print(flush=True)


def _now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def _next_numbered(folder, pattern, template, start=1):
    used = (
        {int(m.group(1)) for p in folder.iterdir() if (m := re.fullmatch(pattern, p.name))}
        if folder.exists()
        else set()
    )
    number = start
    while number in used:
        number += 1
    return folder / template.format(number), number


def _yes(answer, default):
    answer = answer.strip().lower()
    return default if not answer else answer.startswith("y")


def _relative(path, folder):
    try:
        return str(path.resolve().relative_to(folder.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def resolve_inputs(folder, options):
    """Work out restore, expected target and baseline from options and experiment.json."""
    experiment_path = folder / "experiment.json"
    experiment = json.loads(experiment_path.read_text()) if experiment_path.exists() else {}
    restore_path = folder / experiment.get("restore_file", "restore.wav")
    do_restore = options.restore if options.restore is not None else restore_path.exists()
    if do_restore and not restore_path.exists():
        raise ValueError(f"No restore WAV at {restore_path}")
    expected = options.expected
    if expected is None and experiment.get("expected_artifact"):
        expected = folder / experiment["expected_artifact"]
    if expected is None and do_restore and (folder / "edited.symbols.npz").exists():
        expected = folder / "edited.symbols.npz"
    baseline = options.baseline
    if baseline is None and experiment.get("source_artifact"):
        candidate = folder / experiment["source_artifact"]
        baseline = candidate if candidate.exists() else Path(experiment["source_artifact"])
    playback = options.playback_seconds
    if playback is None:
        playback = experiment.get("playback_seconds")
    questions = options.questions
    if questions is None:
        questions = experiment.get("observation_questions") or list(DEFAULT_QUESTIONS)
    instructions = folder / "instructions.md"
    return {
        "experiment": experiment,
        "restore": restore_path if do_restore else None,
        "expected": expected,
        "baseline": baseline,
        "playback_seconds": playback,
        "questions": list(questions),
        "instructions": instructions.read_text() if instructions.exists() else None,
        # Shown at the playback prompt, for what to do on the device while it records.
        "playback_instructions": experiment.get("playback_instructions"),
    }


def backup_summary(entry):
    lines = []
    recording = entry["recording"]
    peaks = recording["signal_peaks_per_channel"]
    lines.append(
        f"  Recorded {recording['duration_seconds']:.1f} s; transfer peaks "
        f"L {peaks[0]:.3f} / R {peaks[1]:.3f}"
    )
    for finding in recording["findings"]:
        lines.append(f"  {finding['severity'].upper()}: {finding['message']}")
    analysis = entry["analysis"]
    if analysis["native"] is None:
        reasons = "; ".join(a["error"] or "failed" for a in analysis["attempts"])
        lines.append(f"  NOT DECODED: {reasons}")
        return lines
    native = analysis["native"]
    lines.append(
        f"  Decoded {native['packet_count']} packets, all checksums valid "
        f"(method: {analysis['method']})"
    )
    target = entry.get("target")
    if target is not None:
        if target["exact_target_body"]:
            lines.append("  MATCHES TARGET EXACTLY")
        else:
            diff = target["differences_from_target"]
            lines.append(f"  DIFFERS FROM TARGET in {diff['change_count']} places:")
            lines.extend("    " + summarize_change(c) for c in diff["changes"][:MAX_LISTED_CHANGES])
    changes = entry.get("changes_from_baseline")
    if changes is not None:
        if changes["identical_body"]:
            lines.append("  Identical to the baseline")
        else:
            lines.append(f"  Changes from baseline ({changes['change_count']}):")
            lines.extend(
                "    " + summarize_change(c) for c in changes["changes"][:MAX_LISTED_CHANGES]
            )
            if changes["change_count"] > MAX_LISTED_CHANGES:
                lines.append(f"    ... {changes['change_count'] - MAX_LISTED_CHANGES} more")
    return lines


def _accept(folder, entry, attempts_dir):
    """Copy the accepted attempt to the standard capture.wav and analysis folder names."""
    wav = attempts_dir / entry["file"]
    write_bytes(folder / "capture.wav", wav.read_bytes())
    derived = folder / "derived"
    derived.mkdir(exist_ok=True)
    analysis_dir, _ = _next_numbered(derived, r"analysis-(\d{3})", "analysis-{:03d}")
    analysis_dir.mkdir()
    source = attempts_dir / entry["analysis_dir"]
    for path in sorted(source.iterdir()):
        write_bytes(analysis_dir / path.name, path.read_bytes())
    return {"capture": "capture.wav", "analysis": _relative(analysis_dir, folder)}


def record_playback(folder, backend, ui, config, seconds, max_attempts=5, instructions=None):
    """Record ordinary playback with immediate protocol checks and retries.

    Every attempt is kept under attempts/. The first attempt without errors is copied
    to playback.wav. If the person declines a retry, the last attempt is copied and
    marked as accepted with findings. `instructions`, when given, are shown before each
    attempt: what to do on the device while the recording runs.
    """
    if (folder / "playback.wav").exists():
        raise ValueError(f"{folder} already has playback.wav")
    attempts_dir = folder / "attempts"
    attempts_dir.mkdir(exist_ok=True)
    entries, accepted = [], None
    for _ in range(max_attempts):
        wav, _number = _next_numbered(attempts_dir, r"playback-(\d{2})\.wav", "playback-{:02d}.wav")
        if instructions:
            ui.say("Playback instructions:")
            ui.say(instructions.strip())
        ui.ask(
            "Press Enter, then press PLAY on the PO-33 about one second later. "
            "Keep every volume unchanged."
        )
        playback = record_fixed(
            backend,
            seconds,
            config.sample_rate,
            config.subtype,
            wait_for_signal=True,
            signal_peak=PLAYBACK_SIGNAL_PEAK,
            max_wait_seconds=10.0,
            on_progress=ui.progress,
        )
        if hasattr(ui, "end_progress"):
            ui.end_progress()
        write_bytes(wav, playback.wav_bytes())
        report = dict(playback.report)
        report["findings"] = report["findings"] + playback_findings(
            playback.samples, playback.rate, report["signal_onset_seconds"]
        )
        entry = {"file": wav.name, "sha256": sha256_file(wav), **report}
        entries.append(entry)
        ui.say("Playback recorded; you can stop the pattern.")
        for finding in report["findings"]:
            ui.say(f"  {finding['severity'].upper()}: {finding['message']}")
        if not any(f["severity"] == "error" for f in report["findings"]):
            accepted = entry
            break
        if not _yes(ui.ask("Record the playback again? [Y/n]"), True):
            accepted = {**entry, "accepted_with_findings": True}
            break
    result = {"attempts": entries, "file": None, "accepted": None}
    if accepted:
        write_bytes(folder / "playback.wav", (attempts_dir / accepted["file"]).read_bytes())
        result.update(
            file="playback.wav",
            accepted=accepted["file"],
            accepted_with_findings=accepted.get("accepted_with_findings", False),
            sha256=accepted["sha256"],
        )
    return result


def run_playback_session(folder, backend, ui, config, seconds, max_attempts=5):
    """Record only ordinary playback into an existing experiment folder."""
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError(f"Experiment folder does not exist: {folder}")
    if (folder / "playback.wav").exists():
        raise ValueError(f"{folder} already has playback.wav")
    experiment_path = folder / "experiment.json"
    experiment = json.loads(experiment_path.read_text()) if experiment_path.exists() else {}
    session_path, _ = _next_numbered(
        folder, r"hardware-session-(\d{3})\.json", "hardware-session-{:03d}.json"
    )
    record = {
        "schema": SESSION_SCHEMA,
        "schema_version": 1,
        "kind": "playback_only",
        "experiment": folder.name,
        "started_at": _now(),
        "audio": backend.describe(),
        "config": asdict(config),
        "playback": None,
        "observations": [],
        "interrupted": False,
        "hardware_verified": False,
    }
    try:
        record["playback"] = record_playback(
            folder,
            backend,
            ui,
            config,
            seconds,
            max_attempts,
            instructions=experiment.get("playback_instructions"),
        )
        for question in experiment.get("observation_questions") or []:
            record["observations"].append({"question": question, "answer": ui.ask(question)})
    except KeyboardInterrupt:
        record["interrupted"] = True
        raise
    finally:
        record["finished_at"] = _now()
        write_bytes(session_path, json_bytes(record))
        ui.say(f"Session record: {session_path}")
    return record


def archive_previous_session(folder):
    """Move the copies a previous session accepted, so the folder can be run again.

    capture.wav, derived/analysis-NNN and playback.wav are byte copies of files kept in
    attempts/. Each is checked against the latest session record and its attempt before
    it is moved to attempts/session-NNN-accepted/. Nothing is deleted.
    """
    sessions = sorted(folder.glob("hardware-session-*.json"))
    records = [(path, json.loads(path.read_text())) for path in sessions]
    records = [
        (p, r) for p, r in records if r.get("accepted") or (r.get("playback") or {}).get("file")
    ]
    if not records:
        raise ValueError("No earlier session accepted files in this folder; nothing to retry")
    path, record = records[-1]
    attempts = folder / "attempts"
    target = attempts / f"{path.stem.replace('hardware-', '')}-accepted"
    if target.exists():
        raise ValueError(f"{target} already exists")
    moves = []
    accepted = record.get("accepted")
    if accepted and (folder / "capture.wav").exists():
        attempt = attempts / accepted["attempt"]
        if sha256_file(folder / "capture.wav") != sha256_file(attempt):
            raise ValueError("capture.wav is not a copy of the accepted attempt; not moving it")
        analysis = folder / accepted["analysis"]
        source = attempts / accepted["attempt"].replace(".wav", "-analysis")
        for item in analysis.iterdir():
            if sha256_file(item) != sha256_file(source / item.name):
                raise ValueError(f"{item} differs from its attempt copy; not moving it")
        moves += [
            (folder / "capture.wav", target / "capture.wav"),
            (analysis, target / analysis.name),
        ]
    playback = (record.get("playback") or {}).get("file")
    if playback and (folder / playback).exists():
        attempt = attempts / record["playback"]["accepted"]
        if sha256_file(folder / playback) != sha256_file(attempt):
            raise ValueError("playback.wav is not a copy of the accepted attempt; not moving it")
        moves.append((folder / playback, target / playback))
    target.mkdir()
    for source, destination in moves:
        source.rename(destination)
    derived = folder / "derived"
    if derived.exists() and not any(derived.iterdir()):
        derived.rmdir()
    note = {
        "archived_from_session": path.name,
        "reason": "Folder run again with --retry; these files are byte copies of attempts",
        "moved": [str(d.relative_to(folder)).replace("\\", "/") for _, d in moves],
    }
    write_bytes(target / "note.json", json_bytes(note))
    return target


def reanalyze_session(folder, ui, threshold=ESTABLISHED_THRESHOLD):
    """Re-decode the backups kept by the latest session that accepted none.

    Uses the current analysis (including fallbacks added since the recording). The first
    attempt that decodes, and matches the expected target if there is one, is accepted
    under the standard names. Earlier analyses are kept; new ones get their own folders.
    """
    folder = Path(folder)
    if (folder / "capture.wav").exists():
        raise ValueError(f"{folder} already has capture.wav")
    sessions = sorted(folder.glob("hardware-session-*.json"))
    source = next((p for p in reversed(sessions) if json.loads(p.read_text()).get("backups")), None)
    if source is None:
        raise ValueError("No session with recorded backups in this folder")
    original = json.loads(source.read_text())
    inputs = resolve_inputs(folder, SessionOptions(restore=False))
    expected_frame = (
        decode_artifact(load_artifact(inputs["expected"])) if inputs["expected"] else None
    )
    attempts_dir = folder / "attempts"
    session_path, _ = _next_numbered(
        folder, r"hardware-session-(\d{3})\.json", "hardware-session-{:03d}.json"
    )
    record = {
        "schema": SESSION_SCHEMA,
        "schema_version": 1,
        "kind": "reanalysis",
        "experiment": folder.name,
        "reanalyzed_session": source.name,
        "reanalyzed_session_sha256": sha256_file(source),
        "started_at": _now(),
        "backups": [],
        "accepted": None,
        "playback": original.get("playback"),
        "hardware_verified": False,
    }
    for item in original["backups"]:
        wav = attempts_dir / item["file"]
        if sha256_file(wav) != item["sha256"]:
            raise ValueError(f"{wav} changed since it was recorded")
        analysis_dir, _ = _next_numbered(
            attempts_dir,
            re.escape(wav.stem) + r"-reanalysis-(\d{3})",
            wav.stem + "-reanalysis-{:03d}",
        )
        analysis = analyze_capture(wav, analysis_dir, threshold)
        entry = {
            "file": item["file"],
            "sha256": item["sha256"],
            "recording": item["recording"],
            "analysis_dir": analysis_dir.name,
            "analysis": analysis.report,
        }
        if analysis.decoded and expected_frame is not None:
            entry["target"] = compare_with_target(expected_frame, analysis.frame)
        record["backups"].append(entry)
        ui.say(f"Reanalysis of {item['file']}:")
        for line in backup_summary(entry):
            ui.say(line)
        exact = entry.get("target", {}).get("exact_target_body", True)
        if analysis.decoded and exact:
            record["accepted"] = {"attempt": entry["file"], **_accept(folder, entry, attempts_dir)}
            break
    record["finished_at"] = _now()
    accepted = record["accepted"]
    record["result"] = {
        "backup_decoded": accepted is not None,
        "native_target_exact": None
        if not accepted or expected_frame is None
        else record["backups"][-1]["target"]["exact_target_body"],
        "capture": accepted["capture"] if accepted else None,
        "analysis": accepted["analysis"] if accepted else None,
        "playback": "playback.wav" if (folder / "playback.wav").exists() else None,
    }
    record["observations"] = original.get("observations", [])
    write_bytes(session_path, json_bytes(record))
    ui.say(f"Session record: {session_path}")
    return record


def run_session(folder, backend, ui, config, options):
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError(f"Experiment folder does not exist: {folder}")
    inputs = resolve_inputs(folder, options)
    if options.retry and ((folder / "capture.wav").exists() or (folder / "playback.wav").exists()):
        archived = archive_previous_session(folder)
        ui.say(f"Earlier accepted copies moved to {archived}")
    if (folder / "capture.wav").exists():
        raise ValueError(
            f"{folder} already has capture.wav; use --retry or a fresh experiment folder"
        )
    if inputs["playback_seconds"] and (folder / "playback.wav").exists():
        raise ValueError(f"{folder} already has playback.wav")
    expected_frame = baseline_frame = None
    if inputs["expected"] is not None:
        expected_frame = decode_artifact(load_artifact(inputs["expected"]))
    if inputs["baseline"] is not None:
        baseline_frame = decode_artifact(load_artifact(inputs["baseline"]))
    session_path, _ = _next_numbered(
        folder, r"hardware-session-(\d{3})\.json", "hardware-session-{:03d}.json"
    )
    attempts_dir = folder / "attempts"
    attempts_dir.mkdir(exist_ok=True)

    def file_info(path):
        return (
            None if path is None else {"path": _relative(path, folder), "sha256": sha256_file(path)}
        )

    record = {
        "schema": SESSION_SCHEMA,
        "schema_version": 1,
        "experiment": folder.name,
        "started_at": _now(),
        "audio": backend.describe(),
        "config": asdict(config),
        "inputs": {
            "restore": file_info(inputs["restore"]),
            "expected_artifact": file_info(inputs["expected"]),
            "baseline_artifact": file_info(inputs["baseline"]),
            "decode_threshold": options.threshold,
        },
        "restore": None,
        "backups": [],
        "accepted": None,
        "playback": None,
        "observations": [],
        "interrupted": False,
        "hardware_verified": False,
        "limits": [
            "Software checks cover exact native reception only; they do not confirm sound",
            "Observations are the person's own words, recorded verbatim",
        ],
    }
    try:
        ui.say(f"Hardware session for {folder.name}")
        if inputs["restore"] is None and inputs["instructions"]:
            ui.say("Instructions:")
            ui.say(inputs["instructions"].strip())
            ui.ask("Make the device changes above, then press Enter.")
        if inputs["restore"] is not None:
            if config.input_cable == "unplug":
                ui.say(
                    "Connect the computer output to the PO-33 input, and unplug the PO-33 "
                    "output from the computer, so the restore cannot loop back."
                )
            else:
                ui.say("Connect the computer output to the PO-33 input.")
            ui.ask(f"Press {RECEIVE_BUTTONS} on the PO-33, then press Enter to play the restore.")
            record["restore"] = {
                "started_at": _now(),
                **play_wav(backend, inputs["restore"], config.playback_gain),
            }
            ui.say("Restore playback finished.")
            if config.input_cable == "unplug":
                ui.ask(
                    "Unplug the computer output from the PO-33 input, connect the PO-33 "
                    "output to the computer input, then press Enter."
                )
            if inputs["instructions"]:
                # Device actions between a known restore and the backup.
                ui.say("Instructions:")
                ui.say(inputs["instructions"].strip())
                ui.ask("Make the device changes above, then press Enter.")
        for _ in range(options.max_attempts):
            wav, number = _next_numbered(attempts_dir, r"backup-(\d{2})\.wav", "backup-{:02d}.wav")
            ui.say(f"Recording armed. Press {SEND_BUTTONS} on the PO-33 now.")
            recording = record_transfer(
                backend,
                config.sample_rate,
                config.subtype,
                max_wait_seconds=options.max_wait_seconds,
                on_progress=ui.progress,
            )
            if hasattr(ui, "end_progress"):
                ui.end_progress()
            write_bytes(wav, recording.wav_bytes())
            analysis_dir = attempts_dir / f"backup-{number:02d}-analysis"
            analysis = analyze_capture(wav, analysis_dir, options.threshold)
            entry = {
                "file": wav.name,
                "sha256": sha256_file(wav),
                "recorded_at": _now(),
                "recording": recording.report,
                "analysis_dir": analysis_dir.name,
                "analysis": analysis.report,
            }
            if analysis.decoded and expected_frame is not None:
                entry["target"] = compare_with_target(expected_frame, analysis.frame)
            if analysis.decoded and baseline_frame is not None:
                entry["changes_from_baseline"] = describe_changes(baseline_frame, analysis.frame)
            record["backups"].append(entry)
            ui.say(f"Backup attempt {number}:")
            for line in backup_summary(entry):
                ui.say(line)
            if not analysis.decoded:
                if _yes(ui.ask("Record the backup again? [Y/n]"), True):
                    continue
                break
            exact = entry.get("target", {}).get("exact_target_body", True)
            if exact or not _yes(ui.ask("Record another backup anyway? [y/N]"), False):
                record["accepted"] = {
                    "attempt": entry["file"],
                    **_accept(folder, entry, attempts_dir),
                }
                break
        if inputs["playback_seconds"]:
            record["playback"] = record_playback(
                folder,
                backend,
                ui,
                config,
                float(inputs["playback_seconds"]),
                options.max_attempts,
                instructions=inputs["playback_instructions"],
            )
        for question in inputs["questions"]:
            record["observations"].append({"question": question, "answer": ui.ask(question)})
    except KeyboardInterrupt:
        record["interrupted"] = True
        raise
    finally:
        record["finished_at"] = _now()
        accepted = record["accepted"]
        last = record["backups"][-1] if record["backups"] else None
        record["result"] = {
            "backup_decoded": bool(last and last["analysis"]["native"]),
            "native_target_exact": (
                None
                if not accepted or expected_frame is None
                else next(b for b in record["backups"] if b["file"] == accepted["attempt"])[
                    "target"
                ]["exact_target_body"]
            ),
            "capture": accepted["capture"] if accepted else None,
            "analysis": accepted["analysis"] if accepted else None,
            "playback": (record["playback"] or {}).get("file"),
        }
        write_bytes(session_path, json_bytes(record))
        ui.say(f"Session record: {session_path}")
    return record


def loopback_check(backend, restore_wav, expected_artifact, out_dir, config, threshold=0.0063):
    """Play a restore WAV while recording it back through a patch cable (no device).

    This tests the computer playback path: driver resampling, enhancements, volume
    and clipping. Exact recovery means the PO-33 is offered the intended data.
    """
    from .audio_io import SUBTYPE_DTYPES, Recording, level_findings, load_for_playback

    out_dir = Path(out_dir)
    if out_dir.exists():
        raise ValueError(f"Output folder already exists: {out_dir}")
    samples, rate = load_for_playback(restore_wav)
    if rate != config.sample_rate:
        raise ValueError("Restore WAV rate differs from the configured recording rate")
    dtype = SUBTYPE_DTYPES[config.subtype]
    recorded, flags = backend.playrec(samples, rate, dtype)
    out_dir.mkdir(parents=True)
    peaks = (
        abs(recorded.astype("float64")).max(axis=0) / (32768.0 if dtype == "int16" else 2**31)
    ).tolist()
    recording = Recording(recorded, rate, config.subtype, {})
    wav = out_dir / "loopback.wav"
    write_bytes(wav, recording.wav_bytes())
    analysis = analyze_capture(wav, out_dir / "analysis", threshold)
    report = {
        "restore_wav_sha256": sha256_file(restore_wav),
        "loopback_sha256": sha256_file(wav),
        "audio": backend.describe(),
        "peaks_per_channel": peaks,
        "stream_status_flags": flags,
        "findings": level_findings(peaks, flags),
        "analysis": analysis.report,
        "exact_target_body": None,
        "hardware_verified": False,
    }
    if analysis.decoded:
        target = decode_artifact(load_artifact(expected_artifact))
        report.update(compare_with_target(target, analysis.frame))
    write_bytes(out_dir / "loopback-report.json", json_bytes(report))
    return report
