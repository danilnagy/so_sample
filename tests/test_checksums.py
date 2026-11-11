import numpy as np
import pytest

from po33_re.analysis.checksums import scan_frame_offsets, validate_frame_candidate


def reference_crc(payload, width):
    if width == 16:
        crc = 0
        for value in payload:
            crc ^= value << 8
            for _ in range(8):
                crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 65535
        return crc
    crc = 0xFFFFFFFF
    for value in payload:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


@pytest.mark.parametrize("width,payload_bytes", [(16, 128), (32, 256)])
def test_checksum_search_finds_positive_control_and_corrupted_holdout(width, payload_bytes):
    rng = np.random.default_rng(94)
    frames = []
    for _ in range(80):
        body = rng.integers(0, 256, payload_bytes, dtype=np.uint8).tobytes()
        frames.append(body + reference_crc(body, width).to_bytes(width // 8, "big"))
    data = b"".join(frames)
    frame_size = payload_bytes + width // 8
    _, hits = scan_frame_offsets(data[: 2 * frame_size], payload_bytes, width)
    candidate = {"byte_offset": 0, "initial": 0, "final_xor": 0, "endian": "big"}
    assert candidate in hits
    result = validate_frame_candidate(data, payload_bytes, width, candidate)
    assert result["all_holdout_frames_pass"] and result["distinct_holdout_payloads"] == 64
    corrupted = bytearray(data)
    corrupted[23 * frame_size + 7] ^= 1
    assert (
        validate_frame_candidate(bytes(corrupted), payload_bytes, width, candidate)[
            "holdout_matching_checksums"
        ]
        == 63
    )


def test_checksum_probe_refuses_invented_wrap_and_short_holdout():
    with pytest.raises(ValueError):
        scan_frame_offsets(bytes(130), 128, 16)
    with pytest.raises(ValueError):
        validate_frame_candidate(bytes(260), 128, 16, {"byte_offset": 0}, frames=64)
