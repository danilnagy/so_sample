"""Reject unexplored sources and verify a single offbeat cell plus isolated swing pair."""

import hashlib
import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import Packet, decode_artifact, decode_frame, encode_packets
from po33_re.formats.patterns import pattern_data
from po33_re.modem.symbols import load_artifact
from scripts.check_swing_range_series import series_checks
from scripts.check_swing_timing_recapture import recapture_checks
from scripts.prepare_swing_timing_pair import candidate_packets, target_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/event-040-a-return-swing18"
    if not (folder / "hardware-observation-001.json").exists():
        pytest.skip("Completed physical swing range required")
    obs = json.loads((folder / "hardware-observation-001.json").read_text())
    path = root / obs["artifact_path"]
    assert sha256_file(path) == obs["artifact_sha256"]
    return decode_artifact(load_artifact(path))


@pytest.mark.capture
def test_actual_range_captures_meet_registered_display_and_full_return_predictions(source):
    root = Path(__file__).resolve().parents[1]
    reg = json.loads((root / "experiments/swing-range-series-registration-001.json").read_text())
    frames = [
        decode_artifact(
            load_artifact(
                root
                / "experiments"
                / item["experiment_id"]
                / "derived/analysis-001/capture.symbols.npz"
            )
        )
        for item in reg["expected_capture_sequence"]
    ]
    base = decode_artifact(load_artifact(root / reg["baseline_artifact"]))
    zero = decode_artifact(load_artifact(root / reg["original_zero_artifact"]))
    report = series_checks(base, frames, zero, reg, [0, 9, 18])
    assert report["series_supported"] and all(report["return_hypotheses"].values())
    assert source.encoded_body == base.encoded_body


@pytest.mark.capture
@pytest.mark.parametrize("swing", [0, 6])
def test_candidate_adds_only_copied_sound3_key16_at_step2_preserving_every_other_byte(
    source, swing
):
    target = native(candidate_packets(source, swing))
    assert all(target_checks(source, target, swing).values())
    before, after = pattern_data(source, 1), pattern_data(target, 1)
    assert [i for i, (a, b) in enumerate(zip(before, after)) if a != b] == [54, 55, 56, 786]
    assert after[54:57] == before[582:585] and after[786] == before[962]


@pytest.mark.capture
def test_pair_isolates_one_swing_byte_with_identical_pattern_and_sample_packets(source):
    zero, six = [candidate_packets(source, n) for n in (0, 6)]
    assert [
        (i, j)
        for i, (p, q) in enumerate(zip(zero, six))
        for j, (a, b) in enumerate(zip(p.payload, q.payload))
        if a != b
    ] == [(2, 130)]


@pytest.mark.capture
@pytest.mark.parametrize("swing", [True, -1, 1, 9, 18, 19, 6.0])
def test_unregistered_research_targets_rejected(source, swing):
    with pytest.raises(ValueError, match="registered research"):
        candidate_packets(source, swing)


@pytest.mark.capture
def test_any_other_source_change_prevents_research_write(source):
    packets = list(source.packets)
    data = bytearray(packets[2].payload)
    data[129] = 138
    packets[2] = Packet(0x7D5C, bytes(data))
    with pytest.raises(ValueError, match="Exact independently"):
        candidate_packets(native(packets), 6)


@pytest.mark.capture
def test_expected_swing_with_wrong_offbeat_pitch_fails_recapture(source):
    target = native(candidate_packets(source, 6))
    packets = list(target.packets)
    # Pattern1 starts at packet4; byte786 belongs to its fourth255-byte chunk.
    index = 4 + 786 // 255
    data = bytearray(packets[index].payload)
    assert data[786 % 255] == 0xFF
    data[786 % 255] = 0xF6
    packets[index] = Packet(packets[index].tag, bytes(data))
    leg = {
        "swing_byte": 6,
        "expected_body_sha256": hashlib.sha256(target.encoded_body).hexdigest(),
    }
    checks = recapture_checks(source, target, native(packets), leg)
    assert not checks["entire_recapture_body_matches_target"]
    assert not checks["pattern1_exact_source13_to_empty2_clone"]
    assert not checks["offbeat_and_reference_same_sound3_key16"]


@pytest.mark.capture
def test_correct_swing_and_pattern_cannot_hide_other_global_changes(source):
    target = native(candidate_packets(source, 0))
    packets = list(target.packets)
    data = bytearray(packets[1].payload)
    data[0] ^= 1
    packets[1] = Packet(0x7D5C, bytes(data))
    assert not target_checks(source, native(packets), 0)["first_global_exact"]
