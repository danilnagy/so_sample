import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "check_clean_copy", ROOT / "scripts/check_clean_copy.py"
)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def available_registration():
    path = ROOT / "experiments/clean-copy2-predictions-001.json"
    reg = json.loads(path.read_text(encoding="utf-8"))
    keys = ("reference_artifact", "expected_before_artifact", "expected_after_artifact")
    if any(not (ROOT / reg[k]).exists() for k in keys):
        pytest.skip("Clean-copy symbol fixtures unavailable")
    return path, reg


@pytest.mark.capture
def test_clean_pair_redecode_and_registered_prediction(monkeypatch):
    registration, reg = available_registration()
    monkeypatch.chdir(ROOT)
    manifest = json.loads((ROOT / "tests/fixtures/manifest.json").read_text(encoding="utf-8"))
    records = {e["path"]: e for e in manifest["captures"]}
    for key in ("expected_before_artifact", "expected_after_artifact"):
        path = ROOT / reg[key]
        source = path.parents[2] / "capture.wav"
        if not source.exists():
            pytest.skip("Clean-copy source recording unavailable")
        reviewed = load_artifact(path)
        actual = decode_wav(source, 0.0063)
        assert actual.to_bytes() == reviewed.to_bytes()
        entry = records[source.relative_to(ROOT).as_posix()]
        expected = entry["expected_clean_copy_decode"]
        assert actual.metadata["source_sha256"] == entry["sha256"]
        for ch in ("left", "right"):
            values = getattr(actual, ch + "_symbols")
            assert len(values) == expected["symbols_per_channel"]
            assert hashlib.sha256(values.tobytes()).hexdigest() == expected[ch + "_symbols_sha256"]
            assert (
                actual.metadata["channels"][ch]["boundary_sign_intervals"][
                    "incomplete_final_cycle_bits"
                ]
                == expected["incomplete_final_sign_intervals"][ch]
            )
    report = checker.run(registration)
    assert report["absolute_position_models_applicable"]
    assert report["single_action_interpretation_eligible"]
    assert report["model_results"] == {
        "front_table": "window_prediction_failed",
        "inline_slots": "window_prediction_passed",
    }
    for ch, first in (("left", 177093), ("right", 177092)):
        result = report["channels"][ch]
        assert result["complete_counts"] == [178868, 178900]
        assert result["strict_first_change"] == first
        assert result["reference_to_before"]["complete_arrays_equal"]
    assert all(a["after_same_position_matches"] for a in report["anchors"])


@pytest.mark.capture
def test_before_geometry_failure_cannot_confirm_model(tmp_path, monkeypatch):
    _, reg = available_registration()
    monkeypatch.chdir(ROOT)
    before = load_artifact(Path(reg["expected_before_artifact"]))
    # Break the registered before prefix at a new position; leave the actual
    # copy-change windows and all registered anchors untouched.
    before.left_symbols[50000] ^= np.uint8(1)
    changed_path = tmp_path / "different-before.npz"
    changed_path.write_bytes(before.to_bytes())
    reg["expected_before_artifact"] = str(changed_path)
    changed_registration = tmp_path / "registration.json"
    changed_registration.write_text(json.dumps(reg), encoding="utf-8")
    report = checker.run(changed_registration)
    assert not report["absolute_position_models_applicable"]
    assert not report["single_action_interpretation_eligible"]
    assert set(report["model_results"].values()) == {"inapplicable"}


@pytest.mark.capture
def test_reported_deviation_prevents_clean_interpretation(monkeypatch):
    registration, _ = available_registration()
    monkeypatch.chdir(ROOT)
    report = checker.run(registration, "Extra sound deletion before copying")
    assert report["absolute_position_models_applicable"]
    assert not report["single_action_interpretation_eligible"]
    assert set(report["model_results"].values()) == {"inapplicable"}
    assert report["channels"]["left"]["observed_window_matches"]["inline_slots"]


@pytest.mark.capture
def test_third_copy_capture_matches_independent_terminal_prediction(monkeypatch):
    path = ROOT / "experiments/third-copy-predictions-001.json"
    reg = json.loads(path.read_text(encoding="utf-8"))
    source = ROOT / "experiments/empty-001-e-copy-to-3/capture.wav"
    if not source.exists():
        pytest.skip("Sound3 copy capture unavailable")
    monkeypatch.chdir(ROOT)
    actual = decode_wav(source, 0.0063)
    reviewed = load_artifact(Path(reg["expected_after_artifact"]))
    assert actual.to_bytes() == reviewed.to_bytes()
    entries = json.loads((ROOT / "tests/fixtures/manifest.json").read_text(encoding="utf-8"))
    entry = next(e for e in entries["captures"] if e["path"] == source.relative_to(ROOT).as_posix())
    assert actual.metadata["source_sha256"] == entry["sha256"]
    expected = entry["expected_third_copy_decode"]
    for ch in ("left", "right"):
        values = getattr(actual, ch + "_symbols")
        assert len(values) == expected[ch + "_symbol_count"]
        assert hashlib.sha256(values.tobytes()).hexdigest() == expected[ch + "_symbols_sha256"]
        assert (
            actual.metadata["channels"][ch]["boundary_sign_intervals"][
                "incomplete_final_cycle_bits"
            ]
            == expected["incomplete_final_sign_intervals"][ch]
        )
    report = checker.run(path)
    assert report["record_size_hypothesis_result"] == "predictions_passed"
    assert report["channels"]["left"]["strict_first_change"] == 177133
    assert report["channels"]["right"]["strict_first_change"] == 177132
    assert report["channels"]["left"]["count_increase"] == 22
    assert report["channels"]["right"]["count_increase"] == 21
    assert all(v["actual_after_index"] == 178792 for v in report["terminal_predictions"].values())


@pytest.mark.capture
def test_passing_location_cannot_hide_failed_terminal_prediction(tmp_path, monkeypatch):
    path = ROOT / "experiments/third-copy-predictions-001.json"
    reg = json.loads(path.read_text(encoding="utf-8"))
    if not (ROOT / reg["expected_after_artifact"]).exists():
        pytest.skip("Sound3 copy artifact unavailable")
    monkeypatch.chdir(ROOT)
    # A wrong independent boundary prediction must fail even when locations pass.
    prediction = reg["last_nonzero_increment_predictions"]["left"]
    prediction["expected_after_index"] += 1
    prediction["expected_displacement"] += 1
    wrong = tmp_path / "wrong-terminal-registration.json"
    wrong.write_text(json.dumps(reg), encoding="utf-8")
    report = checker.run(wrong)
    assert report["model_results"]["inline_slots"] == "window_prediction_passed"
    assert report["record_size_hypothesis_result"] == "predictions_failed"
    assert not report["terminal_predictions"]["left"]["after_boundary_matches"]


@pytest.mark.capture
def test_sound3_trim_capture_preserves_shared_content_and_registered_geometry(monkeypatch):
    source = ROOT / "experiments/empty-001-f-sound3-trim-min/capture.wav"
    if not source.exists():
        pytest.skip("Sound3 trim capture unavailable")
    monkeypatch.chdir(ROOT)
    actual = decode_wav(source, 0.0063)
    reviewed = load_artifact(source.parent / "derived/analysis-001/capture.symbols.npz")
    assert actual.to_bytes() == reviewed.to_bytes()
    entries = json.loads((ROOT / "tests/fixtures/manifest.json").read_text(encoding="utf-8"))
    entry = next(e for e in entries["captures"] if e["path"] == source.relative_to(ROOT).as_posix())
    expected = entry["expected_sound3_trim_decode"]
    assert actual.metadata["source_sha256"] == entry["sha256"]
    for ch in ("left", "right"):
        values = getattr(actual, ch + "_symbols")
        assert len(values) == expected[ch + "_symbol_count"]
        assert hashlib.sha256(values.tobytes()).hexdigest() == expected[ch + "_symbols_sha256"]
        assert (
            actual.metadata["channels"][ch]["boundary_sign_intervals"][
                "incomplete_final_cycle_bits"
            ]
            == expected["incomplete_final_sign_intervals"][ch]
        )
    report = checker.run(ROOT / "experiments/sound3-trim-predictions-001.json")
    assert report["registered_prediction_set_result"] == "predictions_passed"
    for ch in ("left", "right"):
        assert report["channels"][ch]["strict_first_change"] == 177147
        assert report["terminal_predictions"][ch]["actual_after_index"] == 178792
    assert all(v["after_same_position_matches"] for v in report["anchors"])


@pytest.mark.capture
def test_size_and_anchors_cannot_hide_corrupted_return_prefix(tmp_path, monkeypatch):
    path = ROOT / "experiments/sound3-trim-return-predictions-001.json"
    reg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("reference_artifact", "return_reference_artifact"):
        if not (ROOT / reg[key]).exists():
            pytest.skip("Trim and original-reference artifacts unavailable")
    monkeypatch.chdir(ROOT)
    # Synthetic validator input: the known original with one extra changed label.
    # This is not a hardware return capture or an edited restore candidate.
    after = load_artifact(Path(reg["return_reference_artifact"]))
    after.left_symbols[177160] ^= np.uint8(1)
    fake_after = tmp_path / "corrupted-return.npz"
    fake_after.write_bytes(after.to_bytes())
    reg["expected_after_artifact"] = str(fake_after)
    fake_registration = tmp_path / "synthetic-return-registration.json"
    fake_registration.write_text(json.dumps(reg), encoding="utf-8")
    report = checker.run(fake_registration)
    assert report["registered_prediction_set_result"] == "predictions_passed"
    assert report["return_prediction_result"] == "predictions_failed"
    assert not report["return_reference"]["channels"]["left"]["expected_prefix_matches"]
    assert report["return_reference"]["channels"]["right"]["expected_prefix_matches"]


@pytest.mark.capture
def test_maximum_trim_capture_preserves_failed_original_return(monkeypatch):
    source = ROOT / "experiments/empty-001-g-sound3-trim-return/capture.wav"
    if not source.exists():
        pytest.skip("Maximum trim capture unavailable")
    monkeypatch.chdir(ROOT)
    actual = decode_wav(source, 0.0063)
    reviewed = load_artifact(source.parent / "derived/analysis-001/capture.symbols.npz")
    assert actual.to_bytes() == reviewed.to_bytes()
    entries = json.loads((ROOT / "tests/fixtures/manifest.json").read_text(encoding="utf-8"))
    entry = next(e for e in entries["captures"] if e["path"] == source.relative_to(ROOT).as_posix())
    expected = entry["expected_sound3_trim_return_decode"]
    assert actual.metadata["source_sha256"] == entry["sha256"]
    for ch in ("left", "right"):
        values = getattr(actual, ch + "_symbols")
        assert len(values) == expected[ch + "_symbol_count"]
        assert hashlib.sha256(values.tobytes()).hexdigest() == expected[ch + "_symbols_sha256"]
        assert (
            actual.metadata["channels"][ch]["boundary_sign_intervals"][
                "incomplete_final_cycle_bits"
            ]
            == expected["incomplete_final_sign_intervals"][ch]
        )
    report = checker.run(ROOT / "experiments/sound3-trim-return-predictions-001.json")
    assert report["single_action_interpretation_eligible"]
    assert report["model_results"]["inline_slots"] == "window_prediction_passed"
    assert report["return_prediction_result"] == "predictions_failed"
    for ch in ("left", "right"):
        result = report["return_reference"]["channels"][ch]
        assert not result["expected_prefix_matches"]
        assert result["full_complete_array_comparison"]["strict_first_change"] == 177148
    assert report["terminal_predictions"]["left"]["actual_after_index"] == 178791
    assert report["terminal_predictions"]["right"]["actual_after_index"] == 178792
    assert all(v["after_same_position_matches"] for v in report["anchors"])


@pytest.mark.capture
def test_copy_return_matches_original_complete_arrays_and_counts(monkeypatch):
    source = ROOT / "experiments/empty-001-h-sound3-copy-return/capture.wav"
    if not source.exists():
        pytest.skip("Sound3 copy return capture unavailable")
    monkeypatch.chdir(ROOT)
    actual = decode_wav(source, 0.0063)
    reviewed = load_artifact(source.parent / "derived/analysis-001/capture.symbols.npz")
    assert actual.to_bytes() == reviewed.to_bytes()
    entries = json.loads((ROOT / "tests/fixtures/manifest.json").read_text(encoding="utf-8"))
    entry = next(e for e in entries["captures"] if e["path"] == source.relative_to(ROOT).as_posix())
    expected = entry["expected_sound3_copy_return_decode"]
    assert actual.metadata["source_sha256"] == entry["sha256"]
    for ch in ("left", "right"):
        values = getattr(actual, ch + "_symbols")
        assert len(values) == expected[ch + "_symbol_count"]
        assert hashlib.sha256(values.tobytes()).hexdigest() == expected[ch + "_symbols_sha256"]
        assert (
            actual.metadata["channels"][ch]["boundary_sign_intervals"][
                "incomplete_final_cycle_bits"
            ]
            == expected["incomplete_final_sign_intervals"][ch]
        )
    report = checker.run(ROOT / "experiments/sound3-copy-return-predictions-001.json")
    assert report["return_prediction_result"] == "predictions_passed"
    for ch in ("left", "right"):
        result = report["return_reference"]["channels"][ch]
        assert result["expected_prefix_matches"]
        assert result["full_complete_array_comparison"]["complete_arrays_equal"]
        assert result["full_complete_array_comparison"]["count_increase"] == 0
