from synthetic_capture import synthetic_packets

from po33_re.formats.packets import Packet, decode_frame, encode_packets
from scripts.check_pattern_chain_observation import (
    global_byte_changes,
    loop_matches,
    only_globals_changed,
)
from scripts.prepare_pattern_chain_observation import MODELS, PATTERN1_HZ, PATTERN5_HZ


def frames():
    base = list(synthetic_packets())
    changed = list(base)
    second = bytearray(changed[2].payload)
    second[100] = 4
    changed[2] = Packet(0x7D5C, bytes(second))
    return (decode_frame(encode_packets(p), start=0) for p in (base, changed))


def test_global_changes_are_listed_and_isolated():
    base, changed = frames()
    assert global_byte_changes(base, changed) == {1: [(100, 100, 4)]}
    assert only_globals_changed(base, changed)


def test_loop_matching():
    steps = {
        k: [PATTERN1_HZ[k - 1], PATTERN5_HZ[k - 1]] * 2 + [PATTERN1_HZ[k - 1]] for k in range(1, 17)
    }
    assert loop_matches(steps, MODELS["chain_1_5"], 20) == [True] * 5
    assert loop_matches(steps, MODELS["chain_5_1"], 20) == [False] * 5


def test_chain_writer_models_differ_on_at_least_two_loops():
    from scripts.prepare_chain_writer_test import MODELS as WRITER_MODELS

    names = list(WRITER_MODELS)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            assert sum(x != y for x, y in zip(WRITER_MODELS[a], WRITER_MODELS[b])) >= 2
