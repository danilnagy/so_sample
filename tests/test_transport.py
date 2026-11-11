import json

import numpy as np
import pytest
import soundfile as sf

from po33_re.cli import main
from po33_re.modem.decode import DEFAULT_THRESHOLD, DecodeFailure, decode_channel, decode_wav
from po33_re.modem.symbols import load_artifact, unpack_symbols

# Hand-defined quarter-cycle signs, independent of any waveform encoder.
WORDS = {3: [1, 1, 0, 0], 2: [1, 0, 0, 1], 0: [0, 0, 1, 1], 1: [0, 1, 1, 0]}


def vector(symbols, amplitude=0.5):
    bits = [0, 1] + [b for s in symbols for b in WORDS[s]] + [1, 0, 1]
    return np.repeat((np.array(bits, dtype=float) * 2 - 1) * amplitude, 8)


def test_independent_all_phase_transitions_and_endpoints():
    expected = [3] + [s for a in range(4) for b in range(4) for s in (a, b)] + [3, 3]
    decoded, report = decode_channel(vector(expected), 249600, DEFAULT_THRESHOLD)
    assert decoded.tolist() == expected
    assert report["boundary_sign_intervals"]["incomplete_final_cycle_bits"] == [1, 0]
    assert report["boundaries"]["acquisition_verified"] is False
    assert report["uncertainty"]["intervals_over_quarter_unit"] == 0


@pytest.mark.parametrize("amplitude", [0.1, 0.4, 0.9])
def test_normalized_amplitude_invariance(amplitude):
    decoded, _ = decode_channel(vector([3, 2, 0, 1, 3], amplitude), 249600, DEFAULT_THRESHOLD)
    assert decoded.tolist() == [3, 2, 0, 1, 3]


def test_silence_and_insufficient_crossings_fail():
    for values in (np.zeros(100), np.full(100, 0.5)):
        with pytest.raises(DecodeFailure):
            decode_channel(values, 48000, DEFAULT_THRESHOLD)


def test_missing_signal_cli_does_not_write_artifacts(tmp_path):
    path, out = tmp_path / "silence.wav", tmp_path / "out.npz"
    sf.write(path, np.zeros((100, 2)), 48000, subtype="PCM_16")
    assert main(["decode", str(path), "--out", str(out)]) == 3
    assert not out.exists()
    for threshold in ("0", "nan", "1"):
        assert main(["decode", str(path), "--out", str(out), "--threshold", threshold]) == 2


def test_stereo_order_cli_export_and_sidecar(tmp_path):
    path, out, report = tmp_path / "vector.wav", tmp_path / "out.npz", tmp_path / "decode.json"
    left = [3, 2, 0, 1, 3]
    right = [3, 0, 2, 1, 0]
    sf.write(path, np.column_stack((vector(left), vector(right))), 249600, subtype="PCM_24")
    args = ["decode", str(path), "--out", str(out), "--report", str(report)]
    assert main(args) == 0
    loaded = load_artifact(out)
    assert loaded.left_symbols.tolist() == left
    assert loaded.right_symbols.tolist() == right
    assert json.loads(report.read_text())["hardware_verified"] is False
    assert main(args) == 2
    packed = tmp_path / "left.bin"
    export = ["export-symbols", str(out), "--channel", "left", "--out", str(packed)]
    assert main(export) == 0
    sidecar = json.loads((tmp_path / "left.bin.json").read_text())
    assert sidecar["symbol_count"] == 5 and sidecar["padding_symbols"] == 3
    assert unpack_symbols(packed.read_bytes(), sidecar["symbol_count"]).tolist() == left
    assert main(export) == 2
    assert main(["decode", str(path), "--out", str(path), "--force"]) == 2


def test_pcm_widths_decode_same_normalized_vector(tmp_path):
    outputs = []
    for subtype in ("PCM_16", "PCM_24", "PCM_32"):
        path = tmp_path / (subtype + ".wav")
        values = vector([3, 0, 1, 2, 3])
        sf.write(path, np.column_stack((values, values)), 249600, subtype=subtype)
        outputs.append(decode_wav(path).left_symbols.tolist())
    assert outputs == [[3, 0, 1, 2, 3]] * 3


def test_explicit_threshold_rejects_low_level_boundary_noise():
    expected = [3, 2, 0, 1, 3]
    noise = np.tile(np.repeat([0.001, -0.001], 8), 4)
    samples = np.r_[noise, vector(expected), noise]
    raw, _ = decode_channel(samples, 249600, DEFAULT_THRESHOLD)
    filtered, _ = decode_channel(samples, 249600, 0.02)
    assert filtered.tolist() == expected
    assert raw.tolist() != expected


def test_negative_start_after_long_silence_is_not_a_signal_gap():
    expected = [3, 2, 0, 1, 3]
    rate = 249600
    recording = np.r_[np.zeros(2 * rate), vector(expected)]
    labels, report = decode_channel(recording, rate, 0.02)
    assert labels.tolist() == expected
    assert report["initial_negative_origin_sample"] == 2 * rate
    assert report["boundaries"]["first_crossing_sample"] == 2 * rate
    assert report["boundary_sign_intervals"]["incomplete_final_cycle_bits"] == [1, 0]


def test_real_long_crossing_gap_still_fails():
    rate = 249600
    recording = np.r_[vector([3, 2, 0, 1, 3]), np.full(2 * rate, 0.5), vector([3, 2, 0, 1, 3])]
    with pytest.raises(DecodeFailure, match="Crossing gap exceeds one second"):
        decode_channel(recording, rate, 0.02)
