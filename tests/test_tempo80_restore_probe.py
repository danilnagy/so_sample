"""Bind generated tempo audio to independent physical states and reject stale restores."""

import json
from pathlib import Path

import pytest

from po33_re.artifacts import sha256_file
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_groups,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_tempo80_restore import restore_checks
from scripts.make_tempo80_restore import tempo80_candidate_packets


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def states():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-tempo80-001"
    if not (directory / "restore-registration.json").exists():
        pytest.skip("Registered generated tempo restore required")
    reg = json.loads((directory / "restore-registration.json").read_text())
    base, genuine, target = [
        decode_artifact(load_artifact(path))
        for path in (
            root / reg["baseline_artifact"],
            root / reg["genuine80_artifact"],
            directory / "edited.symbols.npz",
        )
    ]
    assert sha256_file(root / reg["baseline_artifact"]) == reg["baseline_artifact_sha256"]
    assert sha256_file(root / reg["genuine80_artifact"]) == reg["genuine80_artifact_sha256"]
    return root, directory, base, target, genuine, reg


@pytest.mark.capture
def test_generated_tempo80_wav_decodes_to_complete_independent_genuine80_body(states):
    _, directory, base, target, genuine, reg = states
    assert encode_packets(tempo80_candidate_packets(base)) == genuine.encoded_body
    decoded = decode_artifact(decode_wav(directory / "restore.wav", 0.02))
    controls, fits, exact, _ = restore_checks(base, target, decoded, genuine, reg, 80)
    assert all(controls.values()) and all(fits.values()) and all(exact.values())
    report = json.loads((directory / "software-validation.json").read_text())
    assert report["passed"] and not report["hardware_verified"]


@pytest.mark.capture
def test_stale120_restore_passes_integrity_but_fails_target_and_display_hypotheses(states):
    _, _, base, target, genuine, reg = states
    controls, fits, exact, _ = restore_checks(base, target, base, genuine, reg, 120)
    assert all(controls.values()) and not fits["native_body_changed"]
    assert not exact["entire_recapture_body_matches_supplied_target"]
    assert not exact["displayed_BPM_independently_matches80"]


@pytest.mark.capture
def test_byte_target_alone_does_not_infer_missing_hardware_display_reading(states):
    _, _, base, target, genuine, reg = states
    controls, _, exact, observed = restore_checks(base, target, target, genuine, reg)
    assert all(controls.values()) and exact["entire_recapture_body_matches_supplied_target"]
    assert exact["displayed_BPM_independently_matches80"] is None
    assert observed["display_after_bpm"] is None


@pytest.mark.capture
def test_correct_target_bytes_with_wrong_reported_display_remain_inconsistent(states):
    _, _, base, target, genuine, reg = states
    controls, fits, exact, _ = restore_checks(base, target, target, genuine, reg, 140)
    assert all(controls.values()) and exact["entire_recapture_body_matches_supplied_target"]
    assert not fits["candidate_matches_observed_after_BPM"]
    assert not exact["displayed_BPM_independently_matches80"]


@pytest.mark.capture
def test_sample_corruption_with_correct_tempo_and_checksums_fails_isolation(states):
    _, _, base, target, genuine, reg = states
    packets = list(target.packets)
    index = sound_groups(target)[0][1]
    data = bytearray(packets[index].payload)
    data[27] ^= 1
    packets[index] = Packet(0xEF78, bytes(data))
    controls, fits, exact, _ = restore_checks(base, target, native(packets), genuine, reg, 80)
    assert not controls["all_sample_records_unchanged"]
    assert fits["candidate_matches_observed_after_BPM"]
    assert not exact["entire_recapture_body_matches_independent_genuine80"]


@pytest.mark.capture
def test_research_tempo_candidate_rejects_an_unobserved_source_context(states):
    _, _, base, _, genuine, _ = states
    with pytest.raises(ValueError, match="original120 native state"):
        tempo80_candidate_packets(genuine)
    packets = list(base.packets)
    index = next(i for i, p in enumerate(packets) if p.tag == 0x7D5C)
    data = bytearray(packets[index].payload)
    data[0] ^= 1
    packets[index] = Packet(0x7D5C, bytes(data))
    with pytest.raises(ValueError, match="original120 native state"):
        tempo80_candidate_packets(native(packets))
