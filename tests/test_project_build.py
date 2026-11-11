from po33_re.project_build import DEFAULT_PARAMETERS, pattern_operations


def test_pattern_operations_write_every_sound_and_the_footer():
    spec = {
        "notes": {"8": [1] + [None] * 15, "13": [None, 1] + [None] * 14},
        "parameters": {"8": {"filter": 24}},
        "locks": {"8": {"filter": [None, 40] + [None] * 14}},
        "effects": [None] * 15 + [7],
    }
    ops = pattern_operations(2, spec)
    notes = [o for o in ops if o["operation"] == "set_notes"]
    assert [o["sound"] for o in notes] == list(range(1, 17))
    assert all(o["pattern"] == 2 for o in ops)
    eight = next(o for o in notes if o["sound"] == 8)
    assert eight["parameters"] == {**DEFAULT_PARAMETERS, "filter": 24}
    assert next(o for o in notes if o["sound"] == 1)["keys"] == [None] * 16
    assert [o["operation"] for o in ops if o["operation"] != "set_notes"] == [
        "set_parameter_locks",
        "set_step_effects",
    ]
