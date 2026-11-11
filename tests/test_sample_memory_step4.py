from test_drum_import import empty_frame, hits
from test_sample_memory_step3 import ref, with_records

from po33_re.drum_import import import_drum_kit_packets
from po33_re.formats.packets import decode_frame, encode_packets
from scripts.check_sample_memory_step4 import classify
from scripts.prepare_sample_memory_step4 import ADVERTISED_CODES, MODELS, TOTAL, absolute_decision


def states():
    lender = ref(0, 4096, 0) + bytes(4096)
    records = {0: lender, **{sid: ref(0, 99, 0) for sid in range(24, 40)}}
    source = with_records(empty_frame(), records)
    packets, _ = import_drum_kit_packets(source, 10, hits([600] * 16), None, (10,))
    return source, decode_frame(encode_packets(packets), start=0)


def test_outcomes_are_classified():
    source, target = states()
    assert classify(target, target, source)[0] == "accepted_exact"
    assert classify(source, target, source)[0] == "kept_previous"
    assert classify(empty_frame(), target, source)[0] == "empty"
    assert classify(None, target, source)[0] == "not_decoded"
    partial = with_records(empty_frame(), {0: ref(0, 4096, 0) + bytes(4096)})
    outcome, summary = classify(partial, target, source)
    assert outcome == "other" and summary["total_capacity_codes"] == 4096
    assert 24 in summary["sound_ids_differing_from_target"]


def test_plan_is_past_the_advertised_limit():
    assert TOTAL == 1019904 > ADVERTISED_CODES
    assert MODELS["sound10_key_k"][1] == 100.0 and absolute_decision(350.0)["stored_rate"]
