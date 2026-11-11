import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from synthetic_capture import (
    artifact_from_packets,
    blocks,
    capture_samples,
    pattern_bytes,
    synthetic_packets,
    tone,
)

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.hardware.audio_io import (
    Recording,
    ScriptedBackend,
    feedback_echo,
    level_findings,
    record_fixed,
    record_transfer,
    resolve_device,
)
from po33_re.hardware.changes import describe_changes, sound_slot_hint, summarize_change
from po33_re.hardware.session import HardwareConfig, SessionOptions, run_session
from po33_re.hardware.verify import analyze_capture

NOTE = ("0e0981", 0xF0)


def frame_of(packets):
    return decode_frame(encode_packets(packets), start=0)


class ScriptedUI:
    def __init__(self, answers=()):
        self.answers = list(answers)
        self.prompts, self.lines = [], []

    def say(self, text=""):
        self.lines.append(text)

    def ask(self, text):
        self.prompts.append(text)
        return self.answers.pop(0) if self.answers else ""

    def progress(self, info):
        pass


# Change descriptions


def test_cell_footer_record_and_sound_changes_are_located():
    old = frame_of(synthetic_packets())
    new = frame_of(
        synthetic_packets(
            patterns={2: pattern_bytes([(5, 3, *NOTE)], footer=b"\x6f" + b"\xff" * 7)},
            tempo=100,
            sound_header=(31393).to_bytes(4, "little") + (39393).to_bytes(4, "little") + b"\x00",
        )
    )
    report = describe_changes(old, new)
    assert not report["identical_body"]
    regions = [c["region"] for c in report["changes"]]
    assert regions == ["pattern_cell", "pattern_footer", "record", "sound"]
    cell, footer, record, sound = report["changes"]
    assert (cell["pattern"], cell["step"], cell["sound"]) == (2, 5, 3)
    assert cell["primary"] == ["000000", "0e0981"] and cell["auxiliary"] == ["00", "f0"]
    assert cell["was_empty"]
    assert footer["footer"] == ["ffffffffffffffff", "6fffffffffffffff"]
    assert record["tag"] == "0x7d5c" and record["ordinal"] == 2
    assert record["bytes"] == [{"offset": 129, "old": 120, "new": 100, "name_hint": "tempo_bpm"}]
    assert sound["header"]["new"] == {"start": 31393, "end": 39393, "owner": 0}
    assert "sample_codes" not in sound
    lines = [summarize_change(c) for c in report["changes"]]
    assert lines[0] == ("Pattern 2 step 5 sound 3: primary 000000->0e0981, aux 00->f0 (was empty)")
    assert "tempo_bpm" in lines[2] and "Sound 3" in lines[3]


def test_identical_frames_report_no_changes():
    frame = frame_of(synthetic_packets())
    report = describe_changes(frame, frame)
    assert report == {
        "identical_body": True,
        "packet_counts": [len(frame.packets)] * 2,
        "change_count": 0,
        "changes": [],
    }


def test_sound_slot_hints_only_claim_verified_mappings():
    assert sound_slot_hint(2) == {"slot": 3, "key": None, "verified": True}
    assert sound_slot_hint(8) == {"slot": 9, "key": 1, "verified": True}
    assert sound_slot_hint(24) == {"slot": 10, "key": 1, "verified": True}
    assert sound_slot_hint(25) == {"slot": 10, "key": 2, "verified": False}
    assert sound_slot_hint(40)["slot"] == 11 and not sound_slot_hint(40)["verified"]
    assert sound_slot_hint(200)["slot"] is None


# Recording


def test_transfer_recording_keeps_every_sample_and_stops_after_quiet_tail():
    rate = 44100
    # Modem data is noise-like; a pure tone would look like an echo at every period.
    rng = np.random.default_rng(2)
    data = np.round(rng.uniform(-0.15, 0.15, (2 * rate, 2)) * 32767).astype(np.int16)
    silence = np.zeros((rate, 2), dtype=np.int16)
    samples = np.vstack([silence, data, silence, silence, silence])
    backend = ScriptedBackend(input_blocks=blocks(samples))
    recording = record_transfer(backend, rate, end_quiet_seconds=1.5)
    report = recording.report
    assert report["status"] == "complete"
    assert report["signal_start_seconds"] == pytest.approx(1.0, abs=0.06)
    assert report["trailing_quiet_seconds"] >= 1.5
    assert report["signal_peaks_per_channel"] == pytest.approx([0.15, 0.15], abs=0.002)
    assert report["feedback_echo"]["checked"] and not report["feedback_echo"]["detected"]
    assert report["findings"] == []
    # The recording is the delivered samples, untrimmed, up to the stopping block.
    assert np.array_equal(recording.samples, samples[: len(recording.samples)])
    assert len(recording.samples) >= round(4.5 * rate)


def test_written_wav_preserves_integer_samples(tmp_path):
    samples = tone(0.5, level=0.2)
    path = tmp_path / "r.wav"
    path.write_bytes(Recording(samples, 44100, "PCM_16", {}).wav_bytes())
    data, rate = sf.read(path, dtype="int16", always_2d=True)
    assert rate == 44100 and sf.info(path).subtype == "PCM_16"
    assert np.array_equal(data, samples)


def test_no_signal_stops_with_an_error():
    backend = ScriptedBackend()
    report = record_transfer(backend, max_wait_seconds=0.5).report
    assert report["status"] == "no_signal"
    assert report["signal_start_seconds"] is None
    assert any(f["severity"] == "error" for f in report["findings"])


def test_level_findings_flag_overflow_clipping_and_mono():
    assert level_findings([0.15, 0.14], []) == []
    messages = " ".join(f["message"] for f in level_findings([0.99, 0.1], ["input overflow"]))
    assert "overflow" in messages and "full scale" in messages and "mono" in messages
    assert level_findings([0.15, 0.0], [])[0]["severity"] == "warning"


def test_playback_recording_waits_for_first_sound_and_keeps_lead_in():
    rate = 44100
    samples = tone(10.0, level=0.1, lead_seconds=2.0)
    backend = ScriptedBackend(input_blocks=blocks(samples))
    recording = record_fixed(backend, 3.0, rate, wait_for_signal=True)
    report = recording.report
    assert report["status"] == "complete"
    assert report["signal_onset_seconds"] == pytest.approx(2.0, abs=0.06)
    assert report["duration_seconds"] == pytest.approx(5.0, abs=0.06)
    assert np.array_equal(recording.samples, samples[: len(recording.samples)])


def test_resolve_device_requires_a_unique_stereo_match():
    devices = [
        {
            "index": 1,
            "name": "Microphone (USB Audio)",
            "hostapi": "MME",
            "max_input_channels": 2,
            "max_output_channels": 0,
            "default_input": True,
            "default_output": False,
        },
        {
            "index": 9,
            "name": "Microphone (USB Audio)",
            "hostapi": "Windows WASAPI",
            "max_input_channels": 2,
            "max_output_channels": 0,
            "default_input": False,
            "default_output": False,
        },
        {
            "index": 3,
            "name": "Headset mic",
            "hostapi": "MME",
            "max_input_channels": 1,
            "max_output_channels": 0,
            "default_input": False,
            "default_output": False,
        },
    ]
    assert resolve_device(None, "input", devices=devices)["index"] == 1
    assert resolve_device("usb", "input", "wasapi", devices)["index"] == 9
    assert resolve_device("1", "input", devices=devices)["index"] == 1
    from po33_re.hardware.audio_io import HardwareUnavailable

    with pytest.raises(HardwareUnavailable, match="Several"):
        resolve_device("usb", "input", devices=devices)
    with pytest.raises(HardwareUnavailable, match="No stereo"):
        resolve_device("headset", "input", devices=devices)


# Immediate verification


def write_capture(path, samples):
    path.write_bytes(Recording(samples, 44100, "PCM_16", {}).wav_bytes())
    return path


def test_analysis_decodes_a_capture_into_standard_files(tmp_path):
    packets = synthetic_packets(patterns={1: pattern_bytes([(1, 3, *NOTE)])})
    capture = write_capture(tmp_path / "c.wav", capture_samples(artifact_from_packets(packets)))
    analysis = analyze_capture(capture, tmp_path / "analysis")
    assert analysis.decoded and analysis.report["method"] == "crossing"
    assert analysis.frame.packets == packets
    names = sorted(p.name for p in (tmp_path / "analysis").iterdir())
    assert names == ["capture.symbols.npz", "decode.json", "harness-analysis.json"]
    decode_report = json.loads((tmp_path / "analysis/decode.json").read_text())
    assert decode_report["source_sha256"] == sha256_file(capture)
    assert decode_report["channels"]["left"]["normalized_crossing_threshold"] == 0.0063
    with pytest.raises(ValueError, match="exists"):
        analyze_capture(capture, tmp_path / "analysis")


def test_analysis_reports_undecodable_audio_without_raising(tmp_path):
    rng = np.random.default_rng(3)
    noise = np.round(rng.normal(0, 0.1, (44100 * 2, 2)) * 32767).astype(np.int16)
    capture = write_capture(tmp_path / "noise.wav", noise)
    analysis = analyze_capture(capture, tmp_path / "analysis")
    assert not analysis.decoded
    assert analysis.report["native"] is None
    assert all(not a["passed"] for a in analysis.report["attempts"])
    assert (tmp_path / "analysis/harness-analysis.json").exists()


# Guided session


@pytest.fixture
def experiment(tmp_path):
    source_packets = synthetic_packets(patterns={1: pattern_bytes([(1, 3, *NOTE)])})
    target_packets = synthetic_packets(
        patterns={1: pattern_bytes([(1, 3, *NOTE)]), 2: pattern_bytes([(1, 3, *NOTE)])}
    )
    source, target = artifact_from_packets(source_packets), artifact_from_packets(target_packets)
    folder = tmp_path / "exp"
    folder.mkdir()
    (folder / "edited.symbols.npz").write_bytes(target.to_bytes())
    (tmp_path / "source.symbols.npz").write_bytes(source.to_bytes())
    from po33_re.modem.encode import encode_artifact

    (folder / "restore.wav").write_bytes(encode_artifact(target, 44100, 0.5)[0])
    return {"folder": folder, "source": source, "target": target, "tmp": tmp_path}


def test_session_exact_round_trip_writes_standard_capture_and_record(experiment):
    folder, target = experiment["folder"], experiment["target"]
    backend = ScriptedBackend(
        streams=[blocks(capture_samples(target)), blocks(tone(6.0, lead_seconds=1.0))]
    )
    ui = ScriptedUI(answers=["", "", "", "one tone per loop"])
    options = SessionOptions(
        playback_seconds=4,
        baseline=experiment["tmp"] / "source.symbols.npz",
        questions=["What did you hear?"],
    )
    record = run_session(folder, backend, ui, HardwareConfig(), options)
    assert len(backend.played) == 1
    assert record["result"] == {
        "backup_decoded": True,
        "native_target_exact": True,
        "capture": "capture.wav",
        "analysis": "derived/analysis-001",
        "playback": "playback.wav",
    }
    assert sha256_file(folder / "capture.wav") == sha256_file(folder / "attempts/backup-01.wav")
    artifact = folder / "derived/analysis-001/capture.symbols.npz"
    from po33_re.modem.symbols import load_artifact

    assert decode_artifact(load_artifact(artifact)).packets == decode_artifact(target).packets
    changes = record["backups"][0]["changes_from_baseline"]
    assert [(c["pattern"], c["step"], c["sound"]) for c in changes["changes"]] == [(2, 1, 3)]
    assert record["observations"] == [
        {"question": "What did you hear?", "answer": "one tone per loop"}
    ]
    assert record["playback"]["accepted"] == "playback-01.wav"
    assert record["playback"]["attempts"][0]["signal_onset_seconds"] == pytest.approx(1.0, abs=0.06)
    saved = json.loads((folder / "hardware-session-001.json").read_text())
    assert saved["result"] == record["result"] and saved["hardware_verified"] is False
    assert any("MATCHES TARGET EXACTLY" in line for line in ui.lines)
    with pytest.raises(ValueError, match="already has capture.wav"):
        run_session(folder, ScriptedBackend(), ScriptedUI(), HardwareConfig(), SessionOptions())


def test_session_retries_an_undecodable_backup_and_keeps_both_attempts(experiment):
    folder, target = experiment["folder"], experiment["target"]
    rng = np.random.default_rng(5)
    bad = np.vstack(
        [
            np.round(rng.normal(0, 0.1, (44100 * 3, 2)) * 32767).astype(np.int16),
            np.zeros((44100 * 2, 2), dtype=np.int16),
        ]
    )
    backend = ScriptedBackend(streams=[blocks(bad), blocks(capture_samples(target))])
    ui = ScriptedUI(answers=["", "", "y"])
    record = run_session(
        folder, backend, ui, HardwareConfig(), SessionOptions(playback_seconds=0, questions=[])
    )
    assert [b["analysis"]["native"] is not None for b in record["backups"]] == [False, True]
    assert record["accepted"]["attempt"] == "backup-02.wav"
    assert (folder / "attempts/backup-01.wav").exists()
    assert record["result"]["native_target_exact"] is True
    assert any("Record the backup again" in p for p in ui.prompts)


def test_session_keeps_a_decoded_backup_that_differs_from_the_target(experiment):
    folder = experiment["folder"]
    backend = ScriptedBackend(input_blocks=blocks(capture_samples(experiment["source"])))
    ui = ScriptedUI(answers=["", "", "n"])
    record = run_session(
        folder, backend, ui, HardwareConfig(), SessionOptions(playback_seconds=0, questions=[])
    )
    assert record["result"]["native_target_exact"] is False
    assert record["result"]["capture"] == "capture.wav"
    diff = record["backups"][0]["target"]["differences_from_target"]
    assert diff["changes"][0]["pattern"] == 2 and diff["changes"][0]["now_empty"]
    assert any("DIFFERS FROM TARGET" in line for line in ui.lines)


def test_observation_session_without_restore_describes_device_changes(tmp_path):
    source_packets = synthetic_packets()
    changed = synthetic_packets(patterns={4: pattern_bytes([(9, 7, "0b0000", 0xF3)])}, tempo=137)
    source = artifact_from_packets(source_packets)
    (tmp_path / "base.symbols.npz").write_bytes(source.to_bytes())
    folder = tmp_path / "observe"
    folder.mkdir()
    (folder / "instructions.md").write_text("Add one note on Pattern 4 step 9 with Sound 7.\n")
    backend = ScriptedBackend(input_blocks=blocks(capture_samples(artifact_from_packets(changed))))
    ui = ScriptedUI()
    record = run_session(
        folder,
        backend,
        ui,
        HardwareConfig(),
        SessionOptions(baseline=tmp_path / "base.symbols.npz", questions=[]),
    )
    assert backend.played == [] and record["restore"] is None
    assert any("Add one note" in line for line in ui.lines)
    changes = record["backups"][0]["changes_from_baseline"]["changes"]
    assert [c["region"] for c in changes] == ["pattern_cell", "record"]
    assert record["result"]["native_target_exact"] is None


def test_instructions_after_a_restore_come_before_the_backup(experiment):
    folder = experiment["folder"]
    (folder / "instructions.md").write_text("Chain patterns 1 and 5.")
    backend = ScriptedBackend(input_blocks=blocks(capture_samples(experiment["source"])))
    ui = ScriptedUI(answers=["", "", "", "n"])
    run_session(
        folder, backend, ui, HardwareConfig(), SessionOptions(playback_seconds=0, questions=[])
    )
    assert backend.played
    finished = ui.lines.index("Restore playback finished.")
    shown = ui.lines.index("Chain patterns 1 and 5.")
    armed = next(i for i, line in enumerate(ui.lines) if line.startswith("Recording armed"))
    assert finished < shown < armed
    assert "Make the device changes above, then press Enter." in ui.prompts


def test_interrupted_session_still_writes_its_record(experiment):
    folder = experiment["folder"]

    class InterruptingUI(ScriptedUI):
        def ask(self, text):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_session(folder, ScriptedBackend(), InterruptingUI(), HardwareConfig(), SessionOptions())
    saved = json.loads((folder / "hardware-session-001.json").read_text())
    assert saved["interrupted"] is True and saved["result"]["capture"] is None


def test_hw_run_command_returns_3_when_the_target_differs(experiment):
    from argparse import Namespace

    from po33_re.hw_cli import run_command

    folder = experiment["folder"]
    args = Namespace(
        command="hw",
        hw_command="run",
        config=experiment["tmp"] / "missing-config.json",
        input=None,
        output=None,
        hostapi=None,
        folder=folder,
        new=False,
        no_restore=False,
        expect=None,
        baseline=None,
        playback=None,
        no_playback=True,
        max_attempts=1,
        threshold=0.0063,
        no_questions=True,
        retry=False,
    )
    backend = ScriptedBackend(input_blocks=blocks(capture_samples(experiment["source"])))
    code = run_command(args, backend_factory=lambda config: backend, ui=ScriptedUI(["", "", "n"]))
    assert code == 3


@pytest.mark.capture
def test_real_first_pair_captures_differ_only_in_the_first_footer_byte():
    root = Path("experiments")
    paths = [
        root / f"edited-pattern1-FX-{leg}-first-pair-001/derived/analysis-001/capture.symbols.npz"
        for leg in ("F6", "6F")
    ]
    if not all(p.exists() for p in paths):
        pytest.skip("First-pair capture artifacts are not present")
    from po33_re.modem.symbols import load_artifact

    a, b = (decode_artifact(load_artifact(p)) for p in paths)
    report = describe_changes(a, b)
    assert report["changes"] == [
        {
            "region": "pattern_footer",
            "pattern": 1,
            "footer": ["f6ffffffffffffff", "6fffffffffffffff"],
            "hint": "per-step effect nibbles; F is none, 6 octave up, 7 octave down",
        }
    ]


def test_feedback_echo_is_detected_and_reported_as_an_error():
    rate = 44100
    rng = np.random.default_rng(11)
    clean = rng.normal(0, 0.05, (rate * 6, 2))
    delay = round(0.0045 * rate)
    looped = clean.copy()
    looped[delay:, 0] -= 0.2 * (clean[:-delay, 0] + clean[:-delay, 1])
    as_pcm = [np.round(v * 32767).astype(np.int16) for v in (clean, looped)]
    assert not feedback_echo(as_pcm[0], rate)["detected"]
    echo = feedback_echo(as_pcm[1], rate)
    assert echo["detected"] and echo["lag_ms"] == pytest.approx(4.5, abs=0.05)
    samples = np.vstack(
        [np.zeros((rate, 2), np.int16), as_pcm[1], np.zeros((2 * rate, 2), np.int16)]
    )
    report = record_transfer(ScriptedBackend(input_blocks=blocks(samples)), rate).report
    assert report["feedback_echo"]["detected"]
    assert any(
        "delayed copy" in f["message"] and f["severity"] == "error" for f in report["findings"]
    )


def test_keep_cable_mode_skips_the_unplug_prompt(experiment):
    folder, target = experiment["folder"], experiment["target"]
    backend = ScriptedBackend(streams=[blocks(capture_samples(target))])
    ui = ScriptedUI()
    config = HardwareConfig(input_cable="keep")
    run_session(folder, backend, ui, config, SessionOptions(playback_seconds=0, questions=[]))
    assert not any("Unplug" in p for p in ui.prompts)
    with pytest.raises(ValueError, match="input_cable"):
        bad = experiment["tmp"] / "bad.json"
        bad.write_text('{"input_cable": "maybe"}')
        HardwareConfig.load(bad)


def test_unplug_mode_asks_for_the_cable_change_after_the_restore(experiment):
    folder, target = experiment["folder"], experiment["target"]
    backend = ScriptedBackend(streams=[blocks(capture_samples(target))])
    ui = ScriptedUI()
    run_session(
        folder, backend, ui, HardwareConfig(), SessionOptions(playback_seconds=0, questions=[])
    )
    assert "Unplug the computer output from the PO-33 input" in ui.prompts[1]


def test_playback_gain_scales_the_played_samples_only(tmp_path):
    from po33_re.hardware.audio_io import play_wav

    path = write_capture(tmp_path / "r.wav", tone(0.5, level=0.5, lead_seconds=0.1))
    backend = ScriptedBackend()
    full = play_wav(backend, path)
    half = play_wav(backend, path, 0.5)
    assert full["peak_after_gain"] == pytest.approx(0.5, abs=0.001)
    assert half["peak_after_gain"] == pytest.approx(0.25, abs=0.001)
    played_full, played_half = backend.played[0][0], backend.played[1][0]
    assert played_full.dtype == np.int16
    assert np.allclose(played_half, played_full / 32768.0 * 0.5, atol=1e-6)
    # Silence pads both ends so a host API that stops early cannot cut the transfer.
    original, _ = sf.read(path, dtype="int16", always_2d=True)
    lead, tail = round(0.25 * 44100), 44100
    assert len(played_full) == lead + len(original) + tail
    assert not played_full[:lead].any() and not played_full[-tail:].any()
    assert np.array_equal(played_full[lead : lead + len(original)], original)
    assert full["frames"] == len(original) and full["padding_seconds"] == [0.25, 1.0]
    with pytest.raises(ValueError, match="gain"):
        play_wav(backend, path, 1.5)


def test_playback_checks_flag_late_start_and_level_change():
    from po33_re.hardware.audio_io import playback_findings

    rate = 44100
    good = tone(8.0, level=0.1, lead_seconds=1.0)
    assert playback_findings(good, rate, 1.0) == []
    late = tone(8.0, level=0.1, lead_seconds=6.0)
    assert "6.0 s" in playback_findings(late, rate, 6.0)[0]["message"]
    early = tone(8.0, level=0.1, lead_seconds=0.1)
    assert "0.10 s" in playback_findings(early, rate, 0.1)[0]["message"]
    louder = np.vstack(
        [tone(4.0, level=0.02, lead_seconds=1.0), tone(4.0, level=0.08, lead_seconds=0)]
    )
    assert "changed by 4.0x" in playback_findings(louder, rate, 1.0)[0]["message"]
    assert playback_findings(good, rate, None)[0]["message"] == "No playback sound was detected"


def test_playback_only_session_retries_until_the_protocol_is_met(tmp_path):
    from po33_re.hardware.session import run_playback_session

    folder = tmp_path / "exp"
    folder.mkdir()
    late = blocks(tone(10.0, level=0.1, lead_seconds=6.0))
    good = blocks(tone(10.0, level=0.1, lead_seconds=1.0))
    backend = ScriptedBackend(streams=[late, good])
    ui = ScriptedUI(answers=["", "y", ""])
    record = run_playback_session(folder, backend, ui, HardwareConfig(), 4.0)
    playback = record["playback"]
    assert [a["file"] for a in playback["attempts"]] == ["playback-01.wav", "playback-02.wav"]
    assert playback["accepted"] == "playback-02.wav" and not playback["accepted_with_findings"]
    assert sha256_file(folder / "playback.wav") == sha256_file(folder / "attempts/playback-02.wav")
    assert json.loads((folder / "hardware-session-001.json").read_text())["kind"] == "playback_only"
    with pytest.raises(ValueError, match="already has playback.wav"):
        run_playback_session(folder, ScriptedBackend(), ScriptedUI(), HardwareConfig(), 4.0)


def test_playback_only_session_shows_the_experiment_playback_instructions(tmp_path):
    from po33_re.hardware.session import run_playback_session

    folder = tmp_path / "exp"
    folder.mkdir()
    (folder / "experiment.json").write_text(
        json.dumps(
            {
                "playback_instructions": "Press key 1 four times, then PLAY.",
                "observation_questions": ["Was key 1 audible?"],
            }
        )
    )
    backend = ScriptedBackend(streams=[blocks(tone(10.0, level=0.1, lead_seconds=1.0))])
    ui = ScriptedUI(answers=["", "yes"])
    record = run_playback_session(folder, backend, ui, HardwareConfig(), 4.0)
    assert "Press key 1 four times, then PLAY." in ui.lines
    assert ui.lines.index("Playback instructions:") < len(ui.lines) - 1
    assert record["observations"] == [{"question": "Was key 1 audible?", "answer": "yes"}]


def test_declining_a_retry_keeps_the_last_playback_with_findings(tmp_path):
    from po33_re.hardware.session import run_playback_session

    folder = tmp_path / "exp"
    folder.mkdir()
    backend = ScriptedBackend(streams=[blocks(tone(10.0, level=0.1, lead_seconds=6.0))])
    record = run_playback_session(folder, backend, ScriptedUI(["", "n"]), HardwareConfig(), 4.0)
    assert record["playback"]["accepted_with_findings"] is True
    assert (folder / "playback.wav").exists()


def test_retry_archives_the_previous_accepted_copies_and_runs_again(experiment):
    folder, target, source = experiment["folder"], experiment["target"], experiment["source"]
    first = ScriptedBackend(
        streams=[blocks(capture_samples(source)), blocks(tone(6.0, lead_seconds=1.0))]
    )
    options = SessionOptions(playback_seconds=4, questions=[])
    run_session(folder, first, ScriptedUI(["", "", "n", ""]), HardwareConfig(), options)
    old_capture = sha256_file(folder / "capture.wav")
    with pytest.raises(ValueError, match="--retry"):
        run_session(folder, ScriptedBackend(), ScriptedUI(), HardwareConfig(), options)
    second = ScriptedBackend(
        streams=[blocks(capture_samples(target)), blocks(tone(6.0, lead_seconds=1.0))]
    )
    retry = SessionOptions(playback_seconds=4, questions=[], retry=True)
    record = run_session(folder, second, ScriptedUI(["", "", ""]), HardwareConfig(), retry)
    archive = folder / "attempts/session-001-accepted"
    assert sha256_file(archive / "capture.wav") == old_capture
    assert (archive / "analysis-001/capture.symbols.npz").exists()
    assert (archive / "playback.wav").exists() and (archive / "note.json").exists()
    assert record["result"]["native_target_exact"] is True
    assert record["accepted"]["attempt"] == "backup-02.wav"
    assert sha256_file(folder / "capture.wav") == sha256_file(folder / "attempts/backup-02.wav")
    assert record["playback"]["accepted"] == "playback-02.wav"


def test_leading_label_realignment_recovers_an_extra_carrier_label(tmp_path):
    from po33_re.hardware.verify import realigned_artifacts

    packets = synthetic_packets(patterns={1: pattern_bytes([(1, 3, *NOTE)])})
    artifact = artifact_from_packets(packets)
    left = np.r_[np.uint8(artifact.left_symbols[0]), artifact.left_symbols]
    metadata = json.loads(json.dumps(artifact.metadata))
    metadata["channels"]["left"]["symbol_count"] = len(left)
    from po33_re.modem.symbols import SymbolArtifact

    shifted = SymbolArtifact(left, artifact.right_symbols, metadata)
    with pytest.raises(ValueError):
        decode_artifact(shifted)
    recovered = [
        (d, decode_artifact(a).packets) for d, a in realigned_artifacts(shifted) if _decodes(a)
    ]
    assert recovered[0][0] == {"channel": "left", "dropped_leading_labels": 1}
    assert recovered[0][1] == packets


def _decodes(artifact):
    try:
        decode_artifact(artifact)
    except ValueError:
        return False
    return True


def test_reanalysis_accepts_a_kept_backup_and_writes_a_record(experiment):
    from po33_re.hardware.session import reanalyze_session

    folder = experiment["folder"]
    rng = np.random.default_rng(9)
    bad = np.vstack(
        [
            np.round(rng.normal(0, 0.1, (44100 * 3, 2)) * 32767).astype(np.int16),
            np.zeros((44100 * 2, 2), dtype=np.int16),
        ]
    )
    backend = ScriptedBackend(streams=[blocks(bad)])
    run_session(
        folder,
        backend,
        ScriptedUI(["", "", "n"]),
        HardwareConfig(),
        SessionOptions(playback_seconds=0, questions=[]),
    )
    assert not (folder / "capture.wav").exists()
    # Replace nothing; a reanalysis of an undecodable attempt accepts nothing.
    record = reanalyze_session(folder, ScriptedUI())
    assert record["kind"] == "reanalysis" and record["accepted"] is None
    assert (folder / "attempts/backup-01-reanalysis-001").exists()
