"""Keep second-start hypothesis failures and the new candidate's narrow scope explicit."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    replace_calibrated_reference_end,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_sample_start_quarter import comparison_checks
from scripts.make_quarter_window_candidate import replace_experimental_endpoint, run


@pytest.fixture(scope="module")
def quarter_control():
    root = Path(__file__).resolve().parents[1]
    registration = json.loads(
        (root / "experiments/sound3-start-quarter-predictions-001.json").read_text()
    )
    directory = root / "experiments/event-014-b-sound3-start-quarter"
    capture = directory / "capture.wav"
    if not capture.exists():
        pytest.skip("Genuine second-start capture required")
    assert (
        sha256_file(capture) == "77ff3658428a7de39ebaca89005c2d88977cee24c7b841cab6fe8f6d344b7d24"
    )
    base = decode_artifact(load_artifact(directory / registration["baseline_artifact"]))
    actual = decode_artifact(decode_wav(capture, 0.0063))
    return base, actual, registration


@pytest.mark.capture
def test_independent_second_start_passes_locality_but_rejects_both_endpoint_predictions(
    quarter_control,
):
    checks, hypotheses, packets, changes, values = comparison_checks(*quarter_control)
    assert all(checks.values()) and packets == [375]
    assert [c["offset"] for c in changes] == [0, 1, 4, 5]
    assert values["after"] == {"first_u32le": 11716, "second_u32le": 11827, "owner_id": 0}
    assert hypotheses == {
        "first_field_moves_lower": True,
        "second_field_unchanged": False,
        "second_field_resets_maximum": False,
    }


@pytest.mark.capture
def test_valid_checksums_do_not_hide_changed_backing_codes(quarter_control):
    base, actual, registration = quarter_control
    packets = list(actual.packets)
    index = next(i for i, p in enumerate(packets) if p.tag == 0xEF78 and len(p.payload) > 9)
    payload = bytearray(packets[index].payload)
    payload[20] ^= 1
    packets[index] = Packet(packets[index].tag, bytes(payload))
    changed = decode_frame(bytes(4095) + encode_packets(packets))
    checks, _, _, _, _ = comparison_checks(base, changed, registration)
    assert checks["all_packet_checksums"]
    assert not checks["backing_owner_unchanged"] and not checks["only_reference_packet_changed"]


@pytest.mark.capture
@pytest.mark.parametrize("endpoint", [11828, 19715, 19717, True])
def test_isolated_writer_rejects_other_endpoints(quarter_control, endpoint):
    with pytest.raises(ValueError):
        replace_experimental_endpoint(quarter_control[1], endpoint)


@pytest.mark.capture
def test_second_start_endpoint_matches_the_reviewed_candidate(quarter_control):
    assert replace_calibrated_reference_end(quarter_control[1], 3, 19716) == (
        replace_experimental_endpoint(quarter_control[1], 19716)
    )
    with pytest.raises(ValueError):
        replace_experimental_endpoint(quarter_control[0], 19716)


@pytest.mark.capture
def test_candidate_pipeline_reproduces_reviewed_wav_and_refuses_existing_output(
    quarter_control, tmp_path
):
    directory = tmp_path / "candidate"
    run(directory)
    report = json.loads((directory / "software-validation.json").read_text())
    assert report["passed"] and all(report["checks"].values())
    assert report["hardware_verified"] is False and report["public_writer_scope_changed"] is False
    assert report["expected_body_sha256"] == (
        "933eca1c290f4fcde0718ddf87e342c3f5b059bbb96d070f98fd6145c342699a"
    )
    wav = directory / "restore-sound3-quarter-window.wav"
    assert sha256_file(wav) == "a81d6bb2e2eb9532155d00355933d0eabb9d2e8a1bb92c45a6b50f8249d7db2a"
    with pytest.raises(FileExistsError):
        run(directory)
    assert sha256_file(wav) == report["restore_wav_sha256"]
