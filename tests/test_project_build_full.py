from pathlib import Path

from scripts.check_project_build_full_test import SNARE_PAIR_S, snare_cycle_intervals
from scripts.prepare_project_build_full_test import CHAIN, EXPECTED, melody_sound, spec


def test_spec_covers_every_slot_and_pattern():
    s = spec(Path("x"))
    assert sorted(map(int, s["melodic"])) == list(range(1, 9))
    assert sorted(map(int, s["drums"])) == list(range(9, 17))
    assert all(len(v) == 16 for v in s["drums"].values())
    assert sorted(map(int, s["patterns"])) == list(range(1, 17))
    assert "14" in s["patterns"]["1"]["notes"] and "14" not in s["patterns"]["2"]["notes"]
    assert [melody_sound(p) for p in (1, 8, 9, 16)] == [1, 8, 1, 8]
    assert s["patterns"]["3"]["effects"][15] == 3 and s["patterns"]["16"]["effects"][15] == 1


def test_snare_bursts_give_the_chain_cycle():
    cycle = EXPECTED["chain_cycle_s"]
    snares = []
    for c in range(3):
        base = 1.0 + c * cycle
        snares += [base, base + SNARE_PAIR_S]
    intervals = snare_cycle_intervals(snares)
    assert len(intervals) == 2 and all(abs(i - cycle) < 1e-9 for i in intervals)
    assert len(CHAIN) == 8
