"""Corrected clear inputs distinguish duplicate WAVs from legitimate identical native state."""

import copy
import json
import sys
from pathlib import Path

import pytest

from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts import check_pattern1_fx_corrected_clear as checker


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/pattern1-FX16-corrected-clear-registration-001.json"
    if not path.exists():
        pytest.skip("Corrected clear registration required")
    registration = json.loads(path.read_text())
    source, baseline = [
        decode_artifact(load_artifact(root / registration[name]))
        for name in ("source_artifact", "independent_no_FX_artifact")
    ]
    return root, source, baseline, registration


@pytest.mark.capture
def test_independent_new_capture_with_unchanged_native_FX8_is_a_model_failure_not_duplicate_proof(
    states,
):
    _, source, baseline, registration = states
    report = checker.clear_report(source, source, baseline, registration)
    assert report["actual_native_controls_pass"]
    assert not report["clear_footer_matches_original_prediction"]
    assert not report["clear_matches_independent_baseline_except_global131"]


@pytest.mark.capture
@pytest.mark.parametrize("global_value", [0, 1, 9, 128])
def test_clear_return_preserves_partial_vs_entire_and_narrow_vs_whole_scope(states, global_value):
    _, source, baseline, registration = states
    packets = list(baseline.packets)
    payload = bytearray(packets[2].payload)
    payload[131] = global_value
    packets[2] = Packet(packets[2].tag, bytes(payload))
    actual = decode_frame(bytes(4095) + encode_packets(packets))
    report = checker.clear_report(source, actual, baseline, registration)
    assert report["clear_footer_matches_original_prediction"]
    assert report["clear_matches_independent_baseline_except_global131"]
    assert report["entire_clear_body_and_packets_match_baseline_diagnostic"] is (global_value == 0)
    assert report["footer_plus_global_low4_scope_preserved"] is (global_value < 16)


@pytest.mark.capture
def test_hidden_clear_change_and_stale_baseline_prediction_fail(states):
    _, source, baseline, registration = states
    data = bytearray(pattern_data(baseline, 1))
    data[770] ^= 1
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(baseline, 1, bytes(data)))
    )
    report = checker.clear_report(source, actual, baseline, registration)
    assert report["clear_footer_matches_original_prediction"]
    assert not report["clear_matches_independent_baseline_except_global131"]
    stale = copy.deepcopy(registration)
    stale["independent_no_FX_body_sha256"] = "0" * 64
    assert not checker.clear_report(source, baseline, baseline, stale)[
        "independent_baseline_body_matches_registration"
    ]


@pytest.mark.capture
def test_cli_rejects_actual_copied_WAV_before_loading_or_judging_clear_state(
    states, tmp_path, monkeypatch
):
    root, _, _, registration = states
    experiments = tmp_path / "experiments"
    experiments.mkdir()
    folder = experiments / registration["experiment_id"]
    folder.mkdir()
    (folder / "capture.wav").write_bytes((root / registration["source_capture"]).read_bytes())
    (experiments / "pattern1-FX16-corrected-clear-registration-001.json").write_text(
        json.dumps(registration)
    )
    monkeypatch.setattr(
        checker, "__file__", str(tmp_path / "scripts/check_pattern1_fx_corrected_clear.py")
    )
    monkeypatch.setattr(sys, "argv", ["check_pattern1_fx_corrected_clear"])
    with pytest.raises(ValueError, match="known duplicate FX8 WAV"):
        checker.main()
    assert not (folder / "corrected-clear-results-001.json").exists()
