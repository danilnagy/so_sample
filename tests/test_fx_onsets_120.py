from scripts.prepare_fx_onsets_120_observation import HELD, SETTINGS, STEP_SECONDS, effects_for


def test_layout_and_settings():
    assert STEP_SECONDS == 0.125 and SETTINGS["step_seconds"] == 0.125
    assert SETTINGS["window_starts_ms"] == [50.0, 90.0]
    assert effects_for(5) == [None] * 16
    assert effects_for(2) == [None] * 4 + [10] * 8 + [None] * 4 and HELD[3] == 12
