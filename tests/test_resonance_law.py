import numpy as np

from scripts.check_resonance_law_test import evaluate, peaks
from scripts.prepare_resonance_law_test import RESONANCE_CODES, step_layout


def test_layout_covers_every_code_with_references():
    layout = step_layout()
    assert len(layout) == 80 and sum(ref for ref, _ in layout) == 5
    assert {c for ref, c in layout if not ref} == set(range(64))
    assert all(codes[0] == 0 for codes in RESONANCE_CODES.values())


def test_peak_hypotheses_on_synthetic_responses():
    layout = [(True, 0), (False, 0), (False, 31), (False, 63)]
    response = np.zeros((4, 50))
    response[2, 6] = 6.0  # +6 dB at 1400 Hz
    response[3, 6] = 15.0
    table = peaks(response, layout)
    assert table[63]["peak_hz"] == 1400.0
    result = evaluate(response, layout, table)
    assert all(result["hypotheses"].values())
    response[3, 30] = 20.0  # a strong peak far from the edge
    assert not evaluate(response, layout, peaks(response, layout))["hypotheses"]["peak_near_edge"]
