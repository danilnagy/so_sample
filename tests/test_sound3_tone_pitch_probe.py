"""New pitch location hypotheses must reject hidden changes and retain coupled TONE data."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import json_bytes, sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import _replace_pattern_data, pattern_data
from po33_re.formats.volume import set_calibrated_sound3_volume
from po33_re.modem.symbols import load_artifact
from scripts.check_sound3_tone_pitch_probe import location_report


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def baseline():
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/sound3-tone-pitch-down-registration-001.json"
    if not path.exists():
        pytest.skip("Pitch probe registration required")
    registration = json.loads(path.read_text())
    source_path = root / registration["source_artifact"]
    assert sha256_file(source_path) == registration["source_artifact_sha256"]
    return root, decode_artifact(load_artifact(source_path)), registration


def changed_pitch(source):
    data = bytearray(pattern_data(source, 1))
    # Independent mixed values expose a possible recorded ramp without guessing endpoints.
    for step, value in ((0, 12), (1, 8), (4, 3), (8, 2), (12, 1)):
        data[48 * step + 6] = (data[48 * step + 6] & 192) | value
    return data


@pytest.mark.capture
def test_genuine_post_playback_body_and_source_pins_remain_exact(baseline):
    root, source, registration = baseline
    folder = root / "experiments/event-050-a-sound3-volume36-post-playback"
    observation_path = folder / "hardware-observation-001.json"
    observation = json.loads(observation_path.read_text())
    assert observation["hardware_verified"] and all(observation["checks"].values())
    assert (
        observation["body_sha256"]
        == hashlib.sha256(source.encoded_body).hexdigest()
        == registration["source_body_sha256"]
    )
    assert sha256_file(observation_path) == registration["source_observation_sha256"]
    previous = decode_artifact(
        load_artifact(
            root / "experiments/edited-sound3-volume36-002/derived/analysis-001/capture.symbols.npz"
        )
    )
    assert source.packets == previous.packets and source.encoded_body == previous.encoded_body
    assert (
        registration["registered_before_capture"]
        and registration["raw_endpoint_value_assumed"] is None
    )


@pytest.mark.capture
def test_no_change_stays_an_alternative_without_claiming_a_pitch_field(baseline):
    _, source, registration = baseline
    report = location_report(source, source, registration)
    assert report["control_passed"] and all(report["preservation_checks"].values())
    assert report["location_hypotheses"]["no_serialized_change"]
    assert not any(
        v for k, v in report["location_hypotheses"].items() if k != "no_serialized_change"
    )
    assert report["first_low6_changed_steps"] == []
    assert not report["pitch_scale_confirmed"] and not report["pitch_field_writer_enabled"]


@pytest.mark.capture
def test_strict_pitch_only_retains_ramp_and_public_volume_guard_rejects_new_context(baseline):
    _, source, registration = baseline
    actual = native(_replace_pattern_data(source, 1, bytes(changed_pitch(source))))
    report = location_report(source, actual, registration)
    assert report["control_passed"] and report["location_hypotheses"]["strict_pitch_candidate_only"]
    assert report["first_low6_changed_steps"] == [1, 2, 5, 9, 13]
    assert report["raw_sound3_fields"]["after"]["known_volume_values"] == [36] * 16
    assert not report["uniform_endpoint_required"]
    with pytest.raises(ValueError, match="Unknown Sound3"):
        set_calibrated_sound3_volume(actual, 21)
    json_bytes(report)


@pytest.mark.capture
def test_coupled_volume_is_not_silently_called_pitch_only(baseline):
    _, source, registration = baseline
    data = changed_pitch(source)
    data[6] |= 192
    data[7] |= 15  # Changed volume independently of low-six pitch candidate.
    report = location_report(
        source, native(_replace_pattern_data(source, 1, bytes(data))), registration
    )
    assert not report["location_hypotheses"]["strict_pitch_candidate_only"]
    assert report["location_hypotheses"]["pitch_candidate_plus_known_volume"]
    assert report["raw_sound3_fields"]["after"]["known_volume_values"][0] == 63


@pytest.mark.capture
def test_volume_only_change_cannot_support_the_pitch_candidate(baseline):
    _, source, registration = baseline
    actual = native(set_calibrated_sound3_volume(source, 21))
    report = location_report(source, actual, registration)
    assert not report["location_hypotheses"]["strict_pitch_candidate_only"]
    assert not report["location_hypotheses"]["pitch_candidate_plus_known_volume"]
    assert report["first_low6_changed_steps"] == []


@pytest.mark.capture
@pytest.mark.parametrize("offset", [8, 770])
def test_other_primary_or_auxiliary_change_stays_a_broader_outcome(baseline, offset):
    _, source, registration = baseline
    data = changed_pitch(source)
    data[offset] ^= 1
    report = location_report(
        source, native(_replace_pattern_data(source, 1, bytes(data))), registration
    )
    assert not report["location_hypotheses"]["strict_pitch_candidate_only"]
    assert not report["location_hypotheses"]["pitch_candidate_plus_known_volume"]
    assert report["location_hypotheses"]["sound3_primary_and_auxiliary_changes"]
    assert report["location_hypotheses"]["other_sound3_primary_changes"] is (offset == 8)


@pytest.mark.capture
@pytest.mark.parametrize("damage", ["neighbor", "footer", "other_pattern", "global", "sample"])
def test_unrelated_state_changes_reject_all_sound3_only_location_hypotheses(baseline, damage):
    _, source, registration = baseline
    data = changed_pitch(source)
    if damage in ("neighbor", "footer"):
        data[3 if damage == "neighbor" else 1024] ^= 1
    actual = native(_replace_pattern_data(source, 1, bytes(data)))
    if damage == "other_pattern":
        other = bytearray(pattern_data(actual, 2))
        other[0] ^= 1
        actual = native(_replace_pattern_data(actual, 2, bytes(other)))
    elif damage in ("global", "sample"):
        packets = list(actual.packets)
        index = (
            2
            if damage == "global"
            else next(i for i, p in enumerate(packets) if p.tag == 0xEF78 and len(p.payload) == 255)
        )
        payload = bytearray(packets[index].payload)
        payload[131 if damage == "global" else 15] ^= 1
        packets[index] = Packet(packets[index].tag, bytes(payload))
        actual = native(packets)
    report = location_report(source, actual, registration)
    assert report["control_passed"]
    assert not any(report["location_hypotheses"].values())
