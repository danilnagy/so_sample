"""Verify registration of the public mono import and keep codes/metadata failures separate."""

import json
from pathlib import Path

import pytest

from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
    sound_groups,
)
from po33_re.modem.symbols import load_artifact
from scripts.check_mono_WAV_import_restore import comparison_checks


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    directory = root / "experiments/edited-sound6-mono-WAV-import-001"
    if not (directory / "restore-registration.json").exists():
        pytest.skip("Registered mono44.1k import candidate required")
    reg = json.loads((directory / "restore-registration.json").read_text())
    before = decode_artifact(load_artifact(root / reg["source_artifact"]))
    target = decode_artifact(load_artifact(directory / "edited.symbols.npz"))
    return before, target, reg


@pytest.mark.capture
def test_exact_mono_import_target_passes_all_registered_native_checks(source):
    before, target, reg = source
    checks, fits, observed = comparison_checks(before, target, target, reg)
    assert all(checks.values()) and all(fits.values())
    assert observed["capacity_codes"] == 32768 and observed["window"]["endpoint"] == 17579
    assert sound_data(target, 5)[:9].hex() == "00000000ab44000005"


@pytest.mark.capture
def test_earlier_short_beep_is_not_accepted_as_the_new_mono_sample(source):
    before, target, reg = source
    checks, fits, _ = comparison_checks(before, target, before, reg)
    assert not checks["state_changed_from_baseline"]
    assert not fits["exact_endpoint17579_and_header"]
    assert not fits["imported17579_code_prefix_preserved"]


@pytest.mark.capture
def test_endpoint_change_is_not_mislabeled_as_loss_of_the_supplied_codes(source):
    before, target, reg = source
    packets = list(target.packets)
    index = sound_groups(target)[5][0]
    data = packets[index].payload
    packets[index] = Packet(0xEF78, data[:4] + (17600).to_bytes(4, "little") + data[8:])
    checks, fits, _ = comparison_checks(before, target, native(packets), reg)
    assert all(checks.values()) and fits["all_supplied32768_codes_preserved"]
    assert not fits["exact_endpoint17579_and_header"] and not fits["logical_window_preserved"]


@pytest.mark.capture
def test_used_sample_corruption_is_rejected_even_with_valid_native_checksums(source):
    before, target, reg = source
    packets = list(target.packets)
    index = sound_groups(target)[5][1]
    data = bytearray(packets[index].payload)
    data[19] ^= 1
    packets[index] = Packet(0xEF78, bytes(data))
    checks, fits, _ = comparison_checks(before, target, native(packets), reg)
    assert all(checks.values())
    assert (
        not fits["imported17579_code_prefix_preserved"]
        and not fits["entire_generated_native_body_matches"]
    )
