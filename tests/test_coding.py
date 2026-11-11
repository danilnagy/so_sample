import json

import numpy as np
import pytest

from po33_re.analysis.clock import clock_grid_probe
from po33_re.analysis.coding import (
    berlekamp_massey,
    gf2_rank,
    phase_coordinates,
    recurrence_errors,
    recurrence_probe,
    repeated_prefix,
)
from po33_re.cli import main
from po33_re.modem.symbols import PHASE_CONVENTION, SCHEMA, SymbolArtifact


def test_hand_calculated_recurrence_and_independent_holdout():
    # s[n] = s[n-1] XOR s[n-3], starting 1,0,0; hand-calculated period is seven.
    period = np.array([1, 0, 0, 1, 1, 1, 0], dtype=np.uint8)
    bits = np.tile(period, 8)
    fitted = berlekamp_massey(bits[:28])
    assert fitted["degree"] == 3
    assert fitted["tap_lags"] == [1, 3]
    assert recurrence_errors(bits, [1, 3], 28) == 0
    altered = bits.copy()
    altered[-1] ^= 1
    assert recurrence_errors(altered, [1, 3], 28) == 1
    bounded = berlekamp_massey(bits[:28], max_degree=2)
    assert bounded["complete"] is False
    assert bounded["degree_lower_bound"] == 3


@pytest.mark.parametrize(
    "bits,degree,lags",
    [
        ([0] * 16, 0, []),
        ([1] * 16, 1, [1]),
        ([1, 0] * 8, 2, [2]),
    ],
)
def test_simple_sequences(bits, degree, lags):
    fitted = berlekamp_massey(np.array(bits, dtype=np.uint8))
    assert fitted["degree"] == degree and fitted["tap_lags"] == lags


def test_training_fit_does_not_imply_holdout_support():
    train = np.tile(np.array([1, 0, 0, 1, 1, 1, 0], dtype=np.uint8), 4)
    bits = np.r_[train, np.zeros(28, dtype=np.uint8)]
    report = recurrence_probe(bits, train=28, holdout=28)
    assert report["fitted_degree"] == 3
    assert report["holdout_errors"] > 0
    assert report["small_recurrence_supported"] is False


def test_independent_binary_rank_vectors():
    rows = np.array([[1, 0, 1], [0, 1, 1], [1, 1, 0]], dtype=np.uint8)
    assert gf2_rank(rows) == 2
    assert gf2_rank(np.vstack((rows, np.array([0, 0, 1], dtype=np.uint8)))) == 3
    assert gf2_rank(np.zeros((2, 3), dtype=np.uint8)) == 0


def test_phase_coordinates_and_exact_period_break():
    labels = np.array([3, 2, 0, 1], dtype=np.uint8)
    assert phase_coordinates(labels).tolist() == [[1, 1], [1, 0], [0, 0], [0, 1]]
    repeated = np.tile(np.array([0, 1, 2, 3], dtype=np.uint8), 30)
    repeated[70] = 3
    result = repeated_prefix(repeated, 0, 64, 16)
    assert result["smallest_exact_period_symbols"] == 4
    assert result["first_period_break_symbol"] == 70


def test_invalid_probe_inputs():
    for invalid in (
        np.array([2], dtype=np.uint8),
        np.array([0], dtype=float),
        np.zeros((1, 2), dtype=np.uint8),
    ):
        with pytest.raises(ValueError):
            berlekamp_massey(invalid)
    with pytest.raises(ValueError):
        recurrence_errors(np.zeros(8, dtype=np.uint8), [0], 4)
    with pytest.raises(ValueError):
        recurrence_probe(np.zeros(10, dtype=np.uint8))
    with pytest.raises(ValueError):
        repeated_prefix(np.zeros(10, dtype=np.uint8))


def write_artifact(path, left, right):
    metadata = {
        "schema": SCHEMA,
        "schema_version": 1,
        "phase_convention": PHASE_CONVENTION,
        "channel_order": ["left", "right"],
        "source_sha256": "a" * 64,
        "sample_rate_hz": 44100,
        "decoder_version": "independent-test-vectors",
        "transformations": [],
        "channels": {
            name: {
                "symbol_count": len(values),
                "boundaries": {},
                "discarded_samples": {},
                "uncertainty": {},
            }
            for name, values in (("left", left), ("right", right))
        },
    }
    path.write_bytes(SymbolArtifact(left, right, metadata).to_bytes())


def test_coding_cli_positive_control_and_safe_outputs(tmp_path):
    rng = np.random.default_rng(9)
    labels = np.r_[np.full(9000, 2, dtype=np.uint8), rng.integers(0, 4, 111000, dtype=np.uint8)]
    changed = labels.copy()
    period = np.array([1, 0, 0, 1, 1, 1, 0], dtype=np.uint8)
    sequence = np.resize(period, len(labels) - 9000)
    changed[9000:] ^= sequence << 1
    baseline, variant, output = (
        tmp_path / "base.npz",
        tmp_path / "variant.npz",
        tmp_path / "out.json",
    )
    write_artifact(baseline, labels, labels)
    write_artifact(variant, changed, rng.integers(0, 4, len(labels), dtype=np.uint8))
    args = ["analyze-coding", str(baseline), str(variant), "--out", str(output)]
    assert main(args) == 0
    report = json.loads(output.read_text())
    fitted = report["variants"][0]["coordinate_lanes"]["left_high"]
    assert fitted["fitted_degree"] == 3 and fitted["holdout_errors"] == 0
    assert fitted["small_recurrence_supported"] is True
    assert report["payload_decoded"] is False
    assert main(args) == 2
    original = baseline.read_bytes()
    assert (
        main(["analyze-coding", str(baseline), str(variant), "--out", str(baseline), "--force"])
        == 2
    )
    assert baseline.read_bytes() == original


@pytest.mark.parametrize("rate", [44100, 48000])
def test_clock_grid_known_carrier_and_polarity(rate):
    # Analytic carrier has exactly two quarter intervals per physical zero-crossing gap.
    samples = 0.5 * np.sin(2 * np.pi * 7812.5 * np.arange(40000) / rate)
    first = clock_grid_probe(samples, rate, 0.0063)
    inverted = clock_grid_probe(-samples, rate, 0.0063)
    assert first["interval_disagreements"] == 0
    assert first["grid_negative_intervals"] == 0
    assert first["phase_concentration_median"] > 0.99
    assert first["physical_crossing_count"] == inverted["physical_crossing_count"]
    assert inverted["interval_disagreements"] == 0


def test_clock_probe_requires_actual_signal():
    with pytest.raises(ValueError, match="signal"):
        clock_grid_probe(np.zeros(100), 48000, 0.0063)
    with pytest.raises(ValueError, match="threshold"):
        clock_grid_probe(np.ones(100), 48000, 0)
