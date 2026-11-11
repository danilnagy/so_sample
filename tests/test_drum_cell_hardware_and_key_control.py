"""Verify the genuine drum-cell restore and independent next-key hypotheses."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import (
    _replace_pattern_data,
    clone_drum_cell,
    pattern_data,
    patterns_report,
    remove_drum_cell,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from po33_re.project import _pattern_view, export_project, packets_from_view
from scripts.check_drum_note_key_control import comparison_checks as key_checks
from scripts.validate_drum_cell_recapture import comparison_checks


@pytest.fixture(scope="module")
def accepted_drum_cell():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-drum-cell-copy-001"
    capture, artifact = (
        directory / "capture.wav",
        directory / "derived/analysis-001/capture.symbols.npz",
    )
    if not capture.exists() or not artifact.exists():
        pytest.skip("Genuine generated drum-cell copy recapture required")
    assert (
        sha256_file(capture) == "5de811a38223d7b4f14dfc65ba1ff724ec4a36458c8413196dc71ab9d4d3d648"
    )
    registration = json.loads((directory / "restore-registration.json").read_text())
    source = decode_artifact(load_artifact(directory / registration["source_artifact"]))
    target = decode_artifact(load_artifact(directory / registration["generated_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    key_registration = json.loads(
        (root / "experiments/drum10-step9-key2-predictions-001.json").read_text()
    )
    return source, target, actual, registration, key_registration, capture, artifact


def altered_pattern(frame, offset, value):
    data = bytearray(pattern_data(frame, 1))
    data[offset] = value
    return decode_frame(bytes(4095) + encode_packets(_replace_pattern_data(frame, 1, bytes(data))))


@pytest.mark.capture
def test_genuine_drum_cell_recapture_matches_complete_registered_target(accepted_drum_cell):
    checks, packets, changes, steps = comparison_checks(*accepted_drum_cell[:4])
    assert all(checks.values()) and packets == [5, 7] and steps == [1, 9]
    assert [c["offset"] for c in changes] == [411, 412, 413, 905]
    assert (
        encode_packets(remove_drum_cell(accepted_drum_cell[2], 1, 10, [9]))
        == accepted_drum_cell[0].encoded_body
    )


@pytest.mark.capture
@pytest.mark.parametrize(
    "auxiliary,expected_drum_fit,expected_melodic_fit",
    [(17, True, False), (241, False, True), (18, False, False)],
)
def test_exact_key_predictions_are_independent_of_locality(
    accepted_drum_cell, auxiliary, expected_drum_fit, expected_melodic_fit
):
    actual, registration = accepted_drum_cell[2], accepted_drum_cell[4]
    changed = altered_pattern(actual, 905, auxiliary)
    checks, fits, packets, changes, observed = key_checks(actual, changed, registration)
    assert all(checks.values()) and packets == [7]
    assert fits["auxiliary_preserves_drum_upper_nibble_and_increments_key"] is expected_drum_fit
    assert fits["auxiliary_matches_melodic_key2"] is expected_melodic_fit
    assert fits["only_auxiliary_byte_changes"] is expected_drum_fit
    assert changes == [{"offset": 905, "old": 16, "new": auxiliary}]
    assert observed["after_auxiliary_byte"] == auxiliary


@pytest.mark.capture
def test_changed_primary_does_not_get_forced_to_saved_raw_prediction(accepted_drum_cell):
    actual, registration = accepted_drum_cell[2], accepted_drum_cell[4]
    changed = altered_pattern(actual, 412, 249)
    checks, fits, packets, _, _ = key_checks(actual, changed, registration)
    assert all(checks.values()) and packets == [5]
    assert (
        not fits["primary_remains_observed_drum_pair"] and not fits["only_auxiliary_packet_changes"]
    )


@pytest.mark.capture
@pytest.mark.parametrize("offset,value", [(777, 17), (390, 14), (29, 132), (1024, 0)])
def test_other_note_and_footer_changes_fail_preservation(accepted_drum_cell, offset, value):
    actual, registration = accepted_drum_cell[2], accepted_drum_cell[4]
    changed = altered_pattern(altered_pattern(actual, 905, 17), offset, value)
    checks, _, _, _, _ = key_checks(actual, changed, registration)
    assert checks["all_native_checksums"] and not checks["only_registered_drum_cell_bytes_changed"]
    assert not all(checks.values())


@pytest.mark.capture
def test_no_key_change_is_not_a_successful_replacement_control(accepted_drum_cell):
    actual, registration = accepted_drum_cell[2], accepted_drum_cell[4]
    checks, _, packets, _, _ = key_checks(actual, actual, registration)
    assert packets == [] and not checks["only_registered_drum_cell_bytes_changed"]


@pytest.mark.capture
def test_observed_key2_can_be_projected_but_remains_unsupported_by_key1_only_writers(
    accepted_drum_cell,
):
    hypothetical = altered_pattern(accepted_drum_cell[2], 905, 17)
    with pytest.raises(ValueError):
        clone_drum_cell(hypothetical, 1, 10, 9, [13])
    with pytest.raises(ValueError):
        remove_drum_cell(hypothetical, 1, 10, [9])
    view = _pattern_view(hypothetical, patterns_report(hypothetical)["patterns"][0])
    note = next(
        c for c in view["observed_cells"] if c["candidate_sound_slot"] == 10 and c["step"] == 9
    )
    assert note["auxiliary_byte"] == 17 and note["calibrated_drum_slice_key"] == 2


@pytest.mark.capture
def test_verified_project_preserves_two_drum_notes_melody_and_all_raw_sources(
    accepted_drum_cell, tmp_path
):
    actual, capture, artifact = accepted_drum_cell[2], accepted_drum_cell[5], accepted_drum_cell[6]
    output = tmp_path / "project"
    report = export_project(
        artifact, capture, output, calibrated_windows=True, calibrated_drum_slices=True
    )
    events = json.loads((output / "patterns/01.json").read_text())["observed_cells"]
    assert [
        (e["step"], e["calibrated_drum_slice_key"])
        for e in events
        if e["candidate_sound_slot"] == 10
    ] == [(1, 1), (9, 1)]
    assert [
        (e["step"], e["calibrated_keyboard_key"]) for e in events if e["candidate_sound_slot"] == 3
    ] == [(1, 1), (5, 2), (9, 7), (13, 16)]
    assert (
        packets_from_view(json.loads((output / "source/packets.json").read_text()))
        == actual.packets
    )
    assert sha256_file(output / "source/capture.wav") == sha256_file(capture)
    assert sha256_file(output / "source/capture.symbols.npz") == sha256_file(artifact)
    for name, record in report["files"].items():
        assert sha256_file(output / name) == record["sha256"]
    assert not report["hardware_verified"]
