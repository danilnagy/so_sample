"""Research FILTER restores must reproduce independent whole bodies and reject hidden edits."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_sound3_filter_restore import reception_checks
from scripts.prepare_generated_sound3_filter_pair import fixed_packets


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-filter16-52-registration-001.json"
    if not path.exists():
        pytest.skip("Registered generated FILTER pair required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


@pytest.mark.capture
@pytest.mark.parametrize("index", [0, 1])
def test_waveforms_match_entire_independent_physical_targets_with_no_hardware_claim(states, index):
    root, source, registration = states
    leg = registration["expected_capture_sequence"][index]
    folder = root / "experiments" / leg["experiment_id"]
    target, recovered, independent = [
        decode_artifact(load_artifact(path))
        for path in (
            folder / "edited.symbols.npz",
            folder / "redecoded.symbols.npz",
            root / leg["independent_physical_artifact"],
        )
    ]
    assert (
        encode_packets(fixed_packets(source, leg["raw_filter_value"]))
        == target.encoded_body
        == recovered.encoded_body
        == independent.encoded_body
    )
    assert target.packets == recovered.packets == independent.packets
    assert all(reception_checks(source, target, recovered, leg, registration).values())
    for name, key in (
        ("restore.wav", "restore_wav_sha256"),
        ("edited.symbols.npz", "edited_artifact_sha256"),
        ("software-validation.json", "software_validation_sha256"),
    ):
        assert sha256_file(folder / name) == leg[key]
    report = json.loads((folder / "software-validation.json").read_text())
    assert report["passed"] and not report["hardware_verified"]
    assert registration["registered_before_both_generated_recaptures"]
    assert registration["independent_physical_target_data_already_observed"]


@pytest.mark.capture
@pytest.mark.parametrize("value", [0, 1, 15, 17, 51, 53, 63, True, 16.0, "16"])
def test_only_fixed_observed_filter_codes_are_accepted_by_research_constructor(states, value):
    with pytest.raises(ValueError, match="Only fixed research filter"):
        fixed_packets(states[1], value)


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_unchanged_filter_values_cannot_rescue_hidden_reception_edits(states, offset):
    root, source, registration = states
    leg = registration["expected_capture_sequence"][0]
    target = decode_artifact(
        load_artifact(root / "experiments" / leg["experiment_id"] / "edited.symbols.npz")
    )
    data = bytearray(pattern_data(target, 1))
    data[offset] ^= 4 if offset == 8 else 1
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(target, 1, bytes(data)))
    )
    checks = reception_checks(source, target, actual, leg, registration)
    assert checks["all16_candidate_values_equal_fixed_value"]
    assert not checks["entire_actual_body_matches_target"]
    assert not checks["every_actual_packet_matches_target"]
    assert not all(checks.values())


@pytest.mark.capture
def test_other_source_and_stale_target_hash_are_rejected(states):
    root, source, registration = states
    leg = registration["expected_capture_sequence"][0]
    target = decode_artifact(
        load_artifact(root / "experiments" / leg["experiment_id"] / "edited.symbols.npz")
    )
    with pytest.raises(ValueError, match="Exact genuine uniform63"):
        fixed_packets(target, 52)
    stale = copy.deepcopy(leg)
    stale["expected_body_sha256"] = "0" * 64
    checks = reception_checks(source, target, target, stale, registration)
    assert checks["entire_actual_body_matches_target"]
    assert not checks["target_body_matches_registration"]
