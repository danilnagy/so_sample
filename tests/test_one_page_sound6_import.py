"""Check real nine-page retention and an actual PCM-file import into a smaller buffer."""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.signal import resample_poly

from po33_re.artifacts import sha256_file
from po33_re.audio import load_pcm_wav
from po33_re.formats.packets import (
    Packet,
    decode_artifact,
    decode_frame,
    encode_packets,
    sound_data,
    sound_groups,
)
from po33_re.modem.decode import decode_wav
from po33_re.modem.symbols import load_artifact
from scripts.check_odd_page_sound6_restore import comparison_checks as nine_page_checks
from scripts.check_one_page_sound6_import_restore import comparison_checks
from scripts.make_one_page_sound6_import import import_one_page_sound6


def native(packets):
    return decode_frame(bytes(4095) + encode_packets(packets))


@pytest.fixture(scope="module")
def source():
    root = Path(__file__).resolve().parents[1]
    folder = root / "experiments/edited-sound6-nine-pages-001"
    if not (folder / "capture.wav").exists():
        pytest.skip("Actual nine-page hardware recapture required")
    assert (
        sha256_file(folder / "capture.wav")
        == "4bd755836feb7ac6f1bcaa806838d398dbf58122a2c2a3882a7909f45409150e"
    )
    frame = decode_artifact(decode_wav(folder / "capture.wav", 0.0063))
    candidate_dir = root / "experiments/edited-sound6-one-page-import-001"
    reg = json.loads((candidate_dir / "restore-registration.json").read_text())
    target = decode_artifact(load_artifact(candidate_dir / "edited.symbols.npz"))
    return root, frame, target, reg


@pytest.mark.capture
def test_real_nine_page_restore_has_exact_capacity_codes_and_entire_target_body(source):
    root, actual, _, _ = source
    folder = root / "experiments/edited-sound6-nine-pages-001"
    reg = json.loads((folder / "restore-registration.json").read_text())
    base, target = (
        decode_artifact(load_artifact(root / reg["source_artifact"])),
        decode_artifact(load_artifact(folder / "edited.symbols.npz")),
    )
    checks, fits, _ = nine_page_checks(base, target, actual, reg)
    assert all(checks.values()) and fits["exact_nine_page_capacity36864"]
    assert fits["entire_generated_native_body_matches"]
    assert (
        not fits["rounded_ten_page_capacity40960"] and not fits["unused_page_dropped_capacity32768"]
    )


@pytest.mark.capture
def test_import_uses_saved_PCM_and_matches_complete_candidate_without_gain_normalization(source):
    root, frame, target, _ = source
    wav = root / "experiments/edited-sound6-one-page-import-001/input-sample.wav"
    samples, info = load_pcm_wav(wav)
    assert info["sample_rate_hz"] == 48000 and info["frames"] == 4800
    audio = resample_poly(samples[:, 0], 125, 256)
    assert len(audio) == 2344
    assert encode_packets(import_one_page_sound6(frame, audio)) == target.encoded_body
    codes = sound_data(target, 5)[9:]
    assert len(codes) == 4096 and codes[2344:] == bytes(1752)


@pytest.mark.capture
@pytest.mark.parametrize(
    "audio",
    [
        np.zeros(100, dtype=float),
        np.zeros(2344, dtype=np.uint8),
        np.full(2344, np.nan),
        np.full(2344, 1.01),
        np.zeros((1, 2344)),
    ],
)
def test_invalid_native_audio_is_rejected(source, audio):
    with pytest.raises(ValueError):
        import_one_page_sound6(source[1], audio)


@pytest.mark.capture
def test_shared_owner_rejected_and_unrelated_packets_remain_exact(source):
    _, frame, target, _ = source
    packets = list(frame.packets)
    index = sound_groups(frame)[7][0]
    packets[index] = Packet(0xEF78, sound_data(frame, 5)[:9])
    with pytest.raises(ValueError, match="unshared"):
        import_one_page_sound6(native(packets), np.zeros(2344, dtype=float))
    assert sound_data(frame, 0) == sound_data(target, 0)
    assert sound_data(frame, 3) == sound_data(target, 3)
    assert sound_data(frame, 4) == sound_data(target, 4)


@pytest.mark.capture
def test_checker_accepts_target_and_distinguishes_larger_capacity_with_same_codes(source):
    _, frame, target, reg = source
    checks, fits, _ = comparison_checks(frame, target, target, reg)
    assert all(checks.values()) and fits["exact_one_page_capacity4096"]
    assert fits["all_supplied4096_codes_preserved"] and fits["imported2344_code_prefix_preserved"]
    index = sound_groups(target)[5][-1]
    packets = (
        target.packets[: index + 1]
        + (Packet(0xEF78, bytes(255)),) * 16
        + (Packet(0xEF78, bytes(16)),)
        + target.packets[index + 1 :]
    )
    checks, fits, observed = comparison_checks(frame, target, native(packets), reg)
    assert (
        all(checks.values())
        and fits["larger_buffer_capacity"]
        and observed["sound6_capacity_codes"] == 8192
    )
    assert fits["all_supplied4096_codes_preserved"] and fits["imported2344_code_window_preserved"]
    assert not fits["entire_generated_native_body_matches"]


@pytest.mark.capture
def test_endpoint_change_and_code_corruption_are_separate_outcomes(source):
    _, frame, target, reg = source
    index = sound_groups(target)[5][0]
    packets = list(target.packets)
    data = packets[index].payload
    packets[index] = Packet(0xEF78, data[:4] + (2496).to_bytes(4, "little") + data[8:])
    checks, fits, _ = comparison_checks(frame, target, native(packets), reg)
    assert all(checks.values()) and fits["all_supplied4096_codes_preserved"]
    assert (
        not fits["header_matches2344_endpoint"] and not fits["imported2344_code_window_preserved"]
    )
    packets = list(target.packets)
    changed = bytearray(packets[index].payload)
    changed[109] ^= 1
    packets[index] = Packet(0xEF78, bytes(changed))
    checks, fits, _ = comparison_checks(frame, target, native(packets), reg)
    assert all(checks.values()) and not fits["imported2344_code_prefix_preserved"]
    assert fits["header_matches2344_endpoint"]
