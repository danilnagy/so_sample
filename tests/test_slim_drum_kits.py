import io

import soundfile as sf

from po33_re.drum_import import SLICE_FRAMES
from scripts.prepare_drum_kit_import_test import hit_wav
from scripts.slim_drum_kits import KEY1_TONES, key1_wav, silence_wav


def test_silence_is_the_shortest_accepted_hit():
    samples, rate = sf.read(io.BytesIO(silence_wav()))
    assert rate == 48000 and len(samples) == SLICE_FRAMES[0] * 256 // 125
    assert not samples.any()


def test_key1_tones_match_the_generators_the_tests_used():
    assert key1_wav(16) == hit_wav(1350.0, 6375) and key1_wav(13) == hit_wav(300.0, 6375)
    assert key1_wav(9) == hit_wav(300.0, 1000)
    assert set(KEY1_TONES) == set(range(9, 17))
