import numpy as np
import pytest

from po33_re.analysis.superposition import compare_prediction, predict_joint


def test_fixed_joint_models_and_endpoint_accounting():
    a = np.array([0, 1, 2, 3], dtype=np.uint8)
    b = np.array([1, 2, 3, 0], dtype=np.uint8)
    c = np.array([2, 3, 0, 1], dtype=np.uint8)
    assert predict_joint(a, b, c, "coordinate_xor").tolist() == [3, 0, 1, 2]
    assert predict_joint(a, b, c, "add_mod4").tolist() == [3, 0, 1, 2]
    predicted = predict_joint(a, b, c, "add_mod4")
    result = compare_prediction(predicted, predicted[:-1])
    assert result["shared_span_matches"]
    assert not result["full_counts_and_content_match"]
    actual = predicted.copy()
    actual[2] ^= 1
    assert compare_prediction(predicted, actual)["first_change"] == 2


def test_affine_positive_control_and_nonlinear_counterexample():
    a = np.array([0, 1, 2, 3], dtype=np.uint8)
    first = a ^ np.array([1, 0, 0, 0], dtype=np.uint8)
    second = a ^ np.array([0, 0, 2, 0], dtype=np.uint8)
    joint = np.array([1, 1, 0, 3], dtype=np.uint8)
    assert compare_prediction(predict_joint(a, first, second, "coordinate_xor"), joint)[
        "full_counts_and_content_match"
    ]
    joint[3] ^= 3
    assert not compare_prediction(predict_joint(a, first, second, "coordinate_xor"), joint)[
        "shared_span_matches"
    ]
    with pytest.raises(ValueError):
        predict_joint(a, first, second, "fitted_model")
