import binascii

import numpy as np
import pytest

from po33_re.analysis.whitening import constant_plaintext_runs, stereo_candidate_bytes


@pytest.mark.parametrize("plain", [0, 255])
def test_unknown_crc_seed_and_corrupted_continuation(plain):
    state = 0x1D0F
    wire = []
    for _ in range(20):
        wire.append((plain + (state & 255)) % 256)
        state = binascii.crc_hqx(bytes([plain]), state)
    data = np.array([9, 123, 231] + wire + [81, 17], dtype=np.uint8)
    result = constant_plaintext_runs(data, plain)
    assert any(r["byte_span"] == [3, 23] and r["initial_state"] == 0x1D0F for r in result["runs"])
    # A three-byte seed match alone cannot pass the remaining observations.
    damaged = np.array(wire[:16], dtype=np.uint8)
    damaged[9] ^= 1
    assert constant_plaintext_runs(damaged, plain)["validated_runs"] == 0


def test_constant_wire_is_not_rich_content_evidence():
    assert constant_plaintext_runs(np.zeros(20, dtype=np.uint8), 0)["validated_runs"] == 0
    with pytest.raises(ValueError):
        constant_plaintext_runs(np.zeros(20, dtype=np.float64), 0)


def test_independent_channel_mapping_and_both_stereo_orders():
    left = np.array([3, 2, 0, 1], dtype=np.uint8)
    right = np.array([1, 2, 3, 0], dtype=np.uint8)
    a, b = (0, 1, 2, 3), (2, 0, 3, 1)
    # Hand-calculated bit groups; neither channel is interpreted as payload here.
    assert stereo_candidate_bytes(left, right, a, b, 0, "stereo_symbols").tolist() == [227, 148]
    assert stereo_candidate_bytes(left, right, a, b, 0, "stereo_symbols", True).tolist() == [
        188,
        97,
    ]
    assert stereo_candidate_bytes(left, right, a, b, 0, "stereo_bytes").tolist() == [75, 156]
    assert stereo_candidate_bytes(left, right, a, b, 0, "stereo_bytes", True).tolist() == [156, 75]
