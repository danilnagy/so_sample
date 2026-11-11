import numpy as np
from synthetic_capture import pattern_bytes, synthetic_packets

from po33_re.edits import OPERATIONS
from po33_re.formats.notes import step_parameters
from po33_re.formats.packets import decode_frame, encode_packets
from po33_re.formats.patterns import drum_notes, pattern_data
from scripts.check_param_only_test import evaluate
from scripts.prepare_param_only_test import (
    MODELS,
    NOTE_FILTERS,
    REFERENCE_FILTERS,
    UNLOCKED_STEPS,
    reference_step,
)


def test_parameter_locks_write_parameter_only_cells():
    frame = decode_frame(
        encode_packets(synthetic_packets(patterns={1: pattern_bytes([(1, 16, "0d0981", 0x10)])})),
        start=0,
    )
    _, apply = OPERATIONS["set_parameter_locks"]
    values = [None, 24] + [None] * 14
    edited = decode_frame(
        encode_packets(
            apply(frame, {"pattern": 1, "sound": 16, "parameter": "filter", "values": values})
        ),
        start=0,
    )
    data = pattern_data(edited, 1)
    assert data[768 + 16 + 15] == 0 and data[48 + 45 : 48 + 48] != bytes(3)
    assert drum_notes(edited, 1, 16)[1] is None
    assert step_parameters(edited, 1, 16)[1] is None  # still reads as no note


def test_models_and_references():
    assert [NOTE_FILTERS[s - 1] for s in UNLOCKED_STEPS] == [0, 0, 0, 0]
    assert all(REFERENCE_FILTERS[reference_step(v) - 1] == v for vs in MODELS.values() for v in vs)


def test_evaluation_picks_the_matching_model():
    response = np.zeros((64, 50))
    for c in range(2):
        for i, value in enumerate(REFERENCE_FILTERS):
            if value is not None:
                response[c * 32 + 16 + i] = -value / 2
        for step, value in zip(UNLOCKED_STEPS, MODELS["param_only_sets_value"], strict=True):
            response[c * 32 + step - 1] = -value / 2
    result = evaluate(response)
    assert result["classification"] == "param_only_sets_value"
