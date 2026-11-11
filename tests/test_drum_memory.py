import pytest
from test_drum_import import empty_frame, hits

from po33_re.drum_import import import_drum_kit_packets
from scripts.prepare_drum_memory_test import (
    BASE,
    CAPACITY,
    LENGTH,
    MODELS,
    TOTAL,
    absolute_decision,
    frequencies,
)


def test_plan_reaches_the_registered_total():
    assert -(-16 * LENGTH // 4096) * 4096 == CAPACITY
    assert TOTAL == 675840 and TOTAL < 937500
    assert frequencies(16)[0] == BASE[16] and MODELS["sound16_key_k"][1] == 100.0
    assert absolute_decision(800.2)["stored_rate"]


def test_total_limit_is_enforced_and_configurable():
    frame = empty_frame()
    kit = hits([6375] * 16)
    with pytest.raises(ValueError, match="limit of 50000"):
        import_drum_kit_packets(frame, 13, kit, None, (13,), total_limit=50000)
    _, allocation = import_drum_kit_packets(frame, 13, kit, None, (13,), total_limit=TOTAL)
    assert allocation["total_backing_capacity_codes"] == CAPACITY
