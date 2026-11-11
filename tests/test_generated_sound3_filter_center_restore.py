"""Center return requires the complete independent native body, not just neutral bits."""

import copy
import json
from pathlib import Path

import pytest

from po33_re.formats.packets import decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_generated_sound3_filter_center_restore import center_reception_checks


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-generated-filter63-center-registration-001.json"
    if not path.exists():
        pytest.skip("Registered generated center required")
    registration = json.loads(path.read_text())
    source, target, independent = [
        decode_artifact(load_artifact(root / name))
        for name in (
            registration["source_artifact"],
            "experiments/edited-sound3-filter63-center-001/edited.symbols.npz",
            registration["independent_center_artifact"],
        )
    ]
    return source, target, independent, registration


@pytest.mark.capture
def test_generated_target_and_independent_recorded_center_match_before_reception(states):
    source, target, independent, registration = states
    assert all(center_reception_checks(source, target, independent, registration).values())
    assert registration["registered_before_center_recapture"]
    assert registration["independent_center_data_already_observed"]


@pytest.mark.capture
@pytest.mark.parametrize("offset", [6, 7, 8, 770, 3, 1024])
def test_correct_neutral_fields_do_not_rescue_hidden_return_changes(states, offset):
    source, target, _, registration = states
    data = bytearray(pattern_data(target, 1))
    data[offset] ^= 4 if offset == 8 else 1
    actual = decode_frame(
        bytes(4095) + encode_packets(_replace_pattern_data(target, 1, bytes(data)))
    )
    checks = center_reception_checks(source, target, actual, registration)
    assert checks["all16_filter_fields_match_registered63"]
    assert not checks["entire_actual_body_and_every_packet_match_target"]


@pytest.mark.capture
def test_unchanged_highpass_and_stale_source_or_target_predictions_fail(states):
    source, target, _, registration = states
    assert not all(center_reception_checks(source, target, source, registration).values())
    for field in ("source_body_sha256", "expected_body_sha256"):
        stale = copy.deepcopy(registration)
        stale[field] = "0" * 64
        assert not all(center_reception_checks(source, target, target, stale).values())
