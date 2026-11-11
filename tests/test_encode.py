import io
import json

import numpy as np
import pytest
import soundfile as sf

from po33_re.cli import main
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact, synthesis_block
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import PHASE_CONVENTION, SCHEMA, SymbolArtifact


def fixture(left, right=None):
    left = np.array(left, dtype=np.uint8)
    right = left.copy() if right is None else np.array(right, dtype=np.uint8)
    return SymbolArtifact(
        left,
        right,
        {
            "schema": SCHEMA,
            "schema_version": 1,
            "phase_convention": PHASE_CONVENTION,
            "channel_order": ["left", "right"],
            "sample_rate_hz": 44100,
            "source_sha256": "a" * 64,
            "decoder_version": "independent-test-vector",
            "transformations": [],
            "channels": {
                name: {
                    "symbol_count": len(symbols),
                    "boundaries": {},
                    "discarded_samples": {},
                    "uncertainty": {},
                    "boundary_sign_intervals": {"incomplete_final_cycle_bits": []},
                }
                for name, symbols in (("left", left), ("right", right))
            },
        },
    )


@pytest.mark.parametrize(
    "label,expected",
    [
        (3, [1, 1]),
        (2, [1, -1]),
        (0, [-1, -1]),
        (1, [-1, 1]),
    ],
)
def test_independent_oscillator_values(label, expected):
    # Eighth-cycle sample values are known analytically, before the transition envelope.
    observed = synthesis_block(np.array([label], dtype=np.uint8), np.array([0.125, 0.375]), 0.5)
    assert observed == pytest.approx(np.array(expected) * np.sqrt(0.5) * 0.5)


@pytest.mark.parametrize("rate", [44100, 48000])
@pytest.mark.parametrize("initial", [2, 3])
@pytest.mark.parametrize("final", [0, 1, 2, 3])
def test_all_transitions_and_complete_endpoints(tmp_path, rate, initial, final):
    phases = [initial] * 5 + [s for a in range(4) for b in range(4) for s in (a, b)] + [final]
    right = (
        [initial] * 5 + [s for a in reversed(range(4)) for b in range(4) for s in (a, b)] + [final]
    )
    original = fixture(phases, right)
    waveform, report = encode_artifact(original, rate)
    path = tmp_path / "generated.wav"
    path.write_bytes(waveform)
    recovered = decode_wav(path, 0.02)
    result = compare_artifacts(original, recovered)
    assert result["passed"] is True
    assert result["channels"]["left"]["tail_symbols"] == 0
    assert result["channels"]["right"]["changed_overlap_symbols"] == 0
    assert report["discarded_symbols"] == 0 and report["hardware_verified"] is False
    assert report["acquisition_primer"]["cycles"] == 0.5
    samples, observed_rate = sf.read(io.BytesIO(waveform), always_2d=True)
    assert observed_rate == rate
    assert np.max(np.abs(samples)) <= 0.501
    assert np.all(samples[: round(0.1 * rate)] == 0)
    assert np.all(samples[-round(0.1 * rate) :] == 0)


def test_invalid_inputs_and_incomplete_cycle_rejected():
    for a in (fixture([]), fixture([2], [2, 3]), fixture([0]), fixture([1])):
        with pytest.raises(ValueError):
            encode_artifact(a)
    a = fixture([2, 3])
    a.metadata["channels"]["left"]["boundary_sign_intervals"]["incomplete_final_cycle_bits"] = [
        1,
        1,
    ]
    with pytest.raises(ValueError, match="incomplete"):
        encode_artifact(a)
    for amplitude in (0, -1, 1, float("nan")):
        with pytest.raises(ValueError, match="amplitude"):
            encode_artifact(fixture([2]), amplitude=amplitude)
    with pytest.raises(ValueError, match="sample rate"):
        encode_artifact(fixture([2]), rate=22050)


def test_comparison_retains_count_and_symbol_differences():
    a, b = fixture([2, 3, 0]), fixture([2, 1, 0, 0])
    report = compare_artifacts(a, b)
    assert report["passed"] is False
    assert report["channels"]["left"]["changed_ranges"] == [[1, 2]]
    assert report["channels"]["left"]["tail_symbols"] == 1
    assert report["channels"]["right"]["alignment_shift"] == 0


def test_encode_and_roundtrip_cli_safe_outputs(tmp_path):
    artifact = tmp_path / "symbols.npz"
    artifact.write_bytes(fixture([2, 3, 0, 1, 2, 3], [2, 0, 3, 1, 2, 0]).to_bytes())
    wav, report = tmp_path / "restore.wav", tmp_path / "encode.json"
    args = ["encode", str(artifact), "--out", str(wav), "--report", str(report)]
    assert main(args) == 0
    assert json.loads(report.read_text())["hardware_verified"] is False
    assert main(args) == 2
    before = artifact.read_bytes()
    assert main(["encode", str(artifact), "--out", str(artifact), "--force"]) == 2
    assert artifact.read_bytes() == before
    directory = tmp_path / "roundtrip"
    args = ["roundtrip", str(wav), "--threshold", ".02", "--out-dir", str(directory)]
    assert main(args) == 0
    result = json.loads((directory / "roundtrip.json").read_text())
    assert result["passed"] is True and result["hardware_verified"] is False
    assert main(args) == 2
    assert main(args + ["--force"]) == 0


def test_polarity_and_clock_changes_not_hidden(tmp_path):
    phases = [2] * 10 + np.random.default_rng(4).integers(0, 4, 500).tolist() + [3]
    original = fixture(phases)
    waveform, _ = encode_artifact(original)
    samples, rate = sf.read(io.BytesIO(waveform), always_2d=True)
    path = tmp_path / "changed.wav"
    sf.write(path, -samples, rate, subtype="PCM_16")
    recovered = decode_wav(path, 0.02)
    assert compare_artifacts(original, recovered)["passed"] is False
    sf.write(path, samples, round(rate * 1.2), subtype="PCM_16")
    recovered = decode_wav(path, 0.02)
    assert compare_artifacts(original, recovered)["passed"] is False


def test_failed_roundtrip_exit_code(monkeypatch, tmp_path):
    monkeypatch.setattr("po33_re.cli.run_roundtrip", lambda *args: {"passed": False})
    assert main(["roundtrip", "input.wav", "--out-dir", str(tmp_path / "run")]) == 3


def test_independent_quarter_midpoints_include_next_high_coordinate():
    # Observed from capture: third quarter depends on NEXT high sign, fourth on CURRENT low.
    # For labels [2,0,1,3], this hand-derived sequence differs from whole-phase blending.
    symbols = np.array([2, 0, 1, 3], dtype=np.uint8)
    cycles = (np.arange(4)[:, None] + np.array([0.125, 0.375, 0.625, 0.875])).ravel()
    expected = np.array([[1, -1, 1, 1], [-1, -1, 1, 1], [-1, 1, -1, -1], [1, 1, -1, -1]]).ravel()
    assert synthesis_block(symbols, cycles, 0.5) == pytest.approx(expected * 0.5 / np.sqrt(2))


def test_component_updates_are_continuous():
    symbols = np.array([2, 0, 1, 3], dtype=np.uint8)
    for point in (0.125, 0.375, 1.125, 1.375, 2.125, 2.375):
        values = synthesis_block(symbols, np.array([point - 1e-9, point + 1e-9]), 0.5)
        assert abs(values[1] - values[0]) < 1e-7


@pytest.mark.parametrize("carrier", [0, 9000, float("nan")])
def test_invalid_carrier_rejected(carrier):
    with pytest.raises(ValueError, match="carrier"):
        encode_artifact(fixture([2, 3]), carrier_hz=carrier)
