"""Exercise bounded WAV import, exact hardware replay and meaningful input/context failures."""

import io
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from po33_re.artifacts import sha256_file
from po33_re.cli import main
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
    sound_groups,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.sample_import import import_sound6_packets, prepare_pcm_sample
from scripts.check_one_page_sound6_import_restore import comparison_checks


def pcm_bytes(values, rate=48000, subtype="PCM_16"):
    buffer = io.BytesIO()
    sf.write(buffer, values, rate, format="WAV", subtype=subtype)
    return buffer.getvalue()


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound6-one-page-import-001"
    if not (folder / "capture.wav").exists():
        pytest.skip("Actual one-page sample-import hardware capture required")
    assert (
        sha256_file(folder / "capture.wav")
        == "1c879e3bc19ff8948feb9692d0e05548ad7ad0251577854e3f590857ae3b0c7b"
    )
    actual = decode_artifact(decode_wav(folder / "capture.wav", 0.0063))
    reg = json.loads((folder / "restore-registration.json").read_text())
    before_path = root / reg["source_artifact"]
    before = decode_artifact(load_artifact(before_path))
    empty = decode_artifact(
        load_artifact(
            root
            / "experiments/event-027-b-delete-unshared-sound7/derived/analysis-001/capture.symbols.npz"
        )
    )
    return root, before_path, before, empty, actual, reg


@pytest.mark.capture
def test_actual_import_capture_matches_one_page_endpoint_and_complete_supplied_codes(states):
    root, _, before, _, actual, reg = states
    target = decode_artifact(
        load_artifact(root / "experiments/edited-sound6-one-page-import-001/edited.symbols.npz")
    )
    checks, fits, observed = comparison_checks(before, target, actual, reg)
    assert all(checks.values()) and fits["entire_generated_native_body_matches"]
    assert fits["header_matches2344_endpoint"] and observed["sound6_capacity_codes"] == 4096


@pytest.mark.capture
def test_public_import_from_empty_and_occupied_sources_reproduces_actual_hardware_body(states):
    root, _, occupied, empty, actual, _ = states
    input_bytes = (
        root / "experiments/edited-sound6-one-page-import-001/input-sample.wav"
    ).read_bytes()
    audio, info = prepare_pcm_sample(input_bytes)
    assert info["native_frames"] == 2344
    for frame in (empty, occupied):
        packets, allocation = import_sound6_packets(frame, 6, audio)
        assert encode_packets(packets) == actual.encoded_body
        assert allocation["capacity_codes"] == 4096


@pytest.mark.capture
def test_import_command_replays_accepted_wav_and_refuses_overwrite(states, tmp_path):
    root, path, _, _, _, _ = states
    sample = root / "experiments/edited-sound6-one-page-import-001/input-sample.wav"
    output = tmp_path / "import"
    args = ["import-sample", str(path), str(sample), "--sound", "6", "--out-dir", str(output)]
    source_before, sample_before = path.read_bytes(), sample.read_bytes()
    assert main(args) == 0
    assert (output / "restore.wav").read_bytes() == (
        root / "experiments/edited-sound6-one-page-import-001/restore.wav"
    ).read_bytes()
    report = json.loads((output / "import-report.json").read_text())
    assert report["passed"] and not report["hardware_verified"]
    assert sha256_file(output / "source.symbols.npz") == sha256_file(path)
    assert main(args) == 2
    assert path.read_bytes() == source_before and sample.read_bytes() == sample_before


def test_mono_44100_and_explicit_stereo_policies_preserve_levels_without_normalization():
    mono = np.full(4410, 0.25)
    audio, info = prepare_pcm_sample(pcm_bytes(mono, 44100))
    assert len(audio) == 2344 and info["resampling_ratio"] == [625, 1176]
    assert info["channel_policy"] == "mono" and not info["gain_normalization"]
    assert abs(np.mean(audio[100:-100]) - 0.25) < 1e-4
    stereo = pcm_bytes(np.column_stack((np.full(4800, 0.25), np.full(4800, -0.25))))
    with pytest.raises(ValueError, match="channels differ"):
        prepare_pcm_sample(stereo)
    left, _ = prepare_pcm_sample(stereo, "left")
    right, _ = prepare_pcm_sample(stereo, "right")
    mixed, _ = prepare_pcm_sample(stereo, "mix")
    assert np.array_equal(left, -right) and not np.any(mixed)


@pytest.mark.parametrize(
    "frames,rate,channels,subtype",
    [
        (2400, 48000, 1, "PCM_16"),
        (96000, 48000, 1, "PCM_16"),
        (4800, 32000, 1, "PCM_16"),
        (4800, 48000, 3, "PCM_16"),
        (4800, 48000, 1, "FLOAT"),
    ],
)
def test_unsupported_input_formats_and_duration_bounds_fail(frames, rate, channels, subtype):
    with pytest.raises(ValueError):
        prepare_pcm_sample(pcm_bytes(np.zeros((frames, channels)), rate, subtype))


def test_truncated_wav_is_not_silently_imported():
    data = bytearray(pcm_bytes(np.zeros(4800)))
    index = data.index(b"data") + 4
    size = int.from_bytes(data[index : index + 4], "little")
    data[index : index + 4] = (size + 100).to_bytes(4, "little")
    with pytest.raises(ValueError, match="Truncated|Invalid"):
        prepare_pcm_sample(bytes(data))


@pytest.mark.capture
@pytest.mark.parametrize("slot,capacity", [(True, None), (5, None), (6, True), (6, 8192), (6, 100)])
def test_unknown_slot_and_capacity_choices_are_rejected(states, slot, capacity):
    with pytest.raises(ValueError):
        import_sound6_packets(states[2], slot, np.zeros(2344, dtype=float), capacity)


@pytest.mark.capture
def test_shared_source_and_excess_calibration_budget_are_rejected(states):
    root, _, _, _, _, _ = states
    shared = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound6-to7-copy-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    with pytest.raises(ValueError, match="referrers"):
        import_sound6_packets(shared, 6, np.zeros(2344, dtype=float))
    large = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound4-growth-001/derived/analysis-001/capture.symbols.npz"
        )
    )
    with pytest.raises(ValueError, match="budget"):
        import_sound6_packets(large, 6, np.zeros(2344, dtype=float))


@pytest.mark.capture
def test_reference_destination_and_bad_source_window_are_rejected(states):
    _, _, base, _, _, _ = states
    packets = list(base.packets)
    indices = sound_groups(base)[5]
    first = packets[indices[0]].payload
    packets[indices[0]] = Packet(0xEF78, first[:4] + (100).to_bytes(4, "little") + first[8:])
    with pytest.raises(ValueError, match="layout"):
        import_sound6_packets(native(packets), 6, np.zeros(2344, dtype=float))
    reference_packets = (
        base.packets[: indices[0]]
        + (Packet(0xEF78, sound_data(base, 7)),)
        + base.packets[indices[-1] + 1 :]
    )
    with pytest.raises(ValueError, match="layout"):
        import_sound6_packets(native(reference_packets), 6, np.zeros(2344, dtype=float))


@pytest.mark.capture
def test_44100_longer_mono_import_chooses_smallest_verified_capacity_and_preserves_other_records(
    states,
):
    root, _, _, _, actual, _ = states
    wav = (
        root / "experiments/calibration-mono-WAV-import-001/chirp-300-to-1800hz-0p75s-mono.wav"
    ).read_bytes()
    audio, info = prepare_pcm_sample(wav)
    assert len(audio) == 17579 and info["channel_policy"] == "mono"
    packets, allocation = import_sound6_packets(actual, 6, audio)
    imported = native(packets)
    assert allocation["capacity_codes"] == 32768 and allocation["endpoint"] == 17579
    assert sound_data(imported, 5)[:9].hex() == "00000000ab44000005"
    for selector in (0, 3, 4):
        assert sound_data(imported, selector) == sound_data(actual, selector)


@pytest.mark.capture
def test_invalid_stereo_cli_produces_no_output_folder(states, tmp_path):
    _, path, _, _, _, _ = states
    sample = tmp_path / "stereo.wav"
    sample.write_bytes(pcm_bytes(np.column_stack((np.full(4800, 0.25), np.full(4800, -0.25)))))
    output = tmp_path / "invalid"
    assert (
        main(["import-sample", str(path), str(sample), "--sound", "6", "--out-dir", str(output)])
        == 2
    )
    assert not output.exists()
