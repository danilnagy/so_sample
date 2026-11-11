import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from po33_re.analysis.periodicity import smallest_period
from po33_re.analysis.staggered import phase_increments, staggered_phases
from po33_re.audio import inspect_wav, load_pcm_wav
from po33_re.modem.decode import decode_wav
from po33_re.modem.encode import encode_artifact, legacy_blend_block, synthesis_block
from po33_re.modem.roundtrip import compare_artifacts
from po33_re.modem.symbols import load_artifact, pack_symbols


@pytest.mark.capture
def test_registered_capture_inspection():
    root = Path(__file__).resolve().parents[1]
    captures = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    if not captures:
        pytest.skip("No genuine capture has been registered with a hash and reviewed expectations")
    for entry in captures:
        path = root / entry["path"]
        if not path.exists():
            pytest.skip(f"Genuine capture unavailable: {path}")
        report = inspect_wav(path)
        assert report["source_sha256"] == entry["sha256"]
        for key, value in entry["expected_inspection"].items():
            assert report[key] == value


@pytest.mark.capture
def test_genuine_decoder_independent_runs(tmp_path):
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    eligible = [e for e in entries if "expected_decode" in e and (root / e["path"]).exists()]
    if not eligible:
        pytest.skip("No genuine capture with reviewed decoding expectations is available")
    for index, entry in enumerate(eligible):
        first, second = tmp_path / f"{index}-first.npz", tmp_path / f"{index}-second.npz"
        for output in (first, second):
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "po33_re",
                    "decode",
                    str(root / entry["path"]),
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stderr
        assert first.read_bytes() == second.read_bytes()
        a = load_artifact(first)
        expected = entry["expected_decode"]
        assert a.metadata["source_sha256"] == entry["sha256"]
        assert a.metadata["decoder_version"] == expected["decoder_version"]
        for name in ("left", "right"):
            symbols = getattr(a, name + "_symbols")
            assert len(symbols) == expected[name + "_symbol_count"]
            assert (
                hashlib.sha256(symbols.tobytes()).hexdigest() == expected[name + "_symbols_sha256"]
            )
        l, _ = pack_symbols(a.left_symbols)
        r, _ = pack_symbols(a.right_symbols)
        n = min(len(a.left_symbols) // 4, len(a.right_symbols) // 4)
        retained = np.column_stack(
            (np.frombuffer(l[:n], dtype=np.uint8), np.frombuffer(r[:n], dtype=np.uint8))
        ).tobytes()
        assert hashlib.sha256(retained).hexdigest() == expected["upstream_compatible_sha256"]


@pytest.mark.capture
def test_repeated_capture_threshold_experiment():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    entries = [e for e in entries if "expected_threshold_decode" in e]
    if len(entries) != 3 or not all((root / e["path"]).exists() for e in entries):
        pytest.skip("Three pinned repeated recordings are required for this comparison")
    decoded = []
    for entry in entries:
        expected = entry["expected_threshold_decode"]
        artifact = decode_wav(root / entry["path"], threshold=expected["threshold"])
        assert artifact.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            symbols = getattr(artifact, channel + "_symbols")
            assert len(symbols) == expected[channel + "_symbol_count"]
            assert (
                hashlib.sha256(symbols.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
        decoded.append(artifact)
    for channel in ("left", "right"):
        first, second, third = [getattr(a, channel + "_symbols") for a in decoded]
        assert np.array_equal(second, third)
        assert len(second) == len(first) + 1
        assert np.array_equal(first, second[: len(first)])
        # Endpoint differences are retained explicitly, not normalized away.
        assert second[-1] == (3 if channel == "left" else 0)


@pytest.mark.capture
@pytest.mark.parametrize("rate", [44100, 48000])
def test_genuine_waveform_reconstruction(tmp_path, rate):
    root = Path(__file__).resolve().parents[1]
    path = root / "experiments/baseline-002/capture.wav"
    if not path.exists():
        pytest.skip("Pinned baseline-002 capture required for waveform reconstruction")
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    entry = next(e for e in entries if e["path"] == "experiments/baseline-002/capture.wav")
    source = decode_wav(path, 0.02)
    assert source.metadata["source_sha256"] == entry["sha256"]
    waveform, encoding = encode_artifact(source, rate)
    wav = tmp_path / "restore.wav"
    wav.write_bytes(waveform)
    restored = decode_wav(wav, 0.02)
    result = compare_artifacts(source, restored)
    assert result["passed"] is True
    assert encoding["hardware_verified"] is False
    for channel in ("left", "right"):
        assert result["channels"][channel]["original_symbols"] == 1970367
        assert result["channels"][channel]["changed_overlap_symbols"] == 0
        assert result["channels"][channel]["tail_symbols"] == 0


@pytest.mark.capture
def test_synthesis_matches_independent_recorded_transition_waveform():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    eligible = [
        e for e in entries if "expected_threshold_decode" in e and (root / e["path"]).exists()
    ]
    if not eligible:
        pytest.skip("Pinned genuine captures required for independent waveform comparison")
    for entry in eligible:
        original = decode_wav(root / entry["path"], 0.02)
        samples, info = load_pcm_wav(root / entry["path"])
        assert original.metadata["source_sha256"] == entry["sha256"]
        rate = info["sample_rate_hz"]
        for index, channel in enumerate(("left", "right")):
            symbols = getattr(original, channel + "_symbols")
            crossing = original.metadata["channels"][channel]["boundaries"][
                "acquisition_candidate_sample"
            ]
            period = rate / 7812.5
            origin = crossing + period / 4
            frames = np.arange(int(origin + 30 * period), int(origin + 500 * period))
            cycles = (frames - origin) / period
            actual = samples[frames, index]
            corrected = synthesis_block(symbols, cycles, 0.5)
            rejected_model = legacy_blend_block(symbols, cycles, 0.5)
            correlation = np.corrcoef(actual, corrected)[0, 1]
            assert correlation > 0.95
            assert correlation > np.corrcoef(actual, rejected_model)[0, 1] + 0.3


@pytest.mark.capture
def test_controlled_hardware_recapture_matches_baseline():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    eligible = [e for e in entries if "expected_post_restore_decode" in e]
    if not eligible:
        pytest.skip("Controlled hardware re-capture fixture is unavailable")
    for entry in eligible:
        expected = entry["expected_post_restore_decode"]
        path = root / entry["path"]
        reference = root / expected["baseline_path"]
        if not path.exists() or not reference.exists():
            pytest.skip("Controlled re-capture or baseline recording unavailable")
        first = decode_wav(path, expected["threshold"])
        second = decode_wav(path, expected["threshold"])
        baseline = decode_wav(reference, expected["baseline_threshold"])
        assert first.metadata["source_sha256"] == entry["sha256"]
        assert first.to_bytes() == second.to_bytes()
        for channel in ("left", "right"):
            symbols = getattr(first, channel + "_symbols")
            assert len(symbols) == expected["symbols_per_channel"]
            assert (
                hashlib.sha256(symbols.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
            assert np.array_equal(symbols, getattr(baseline, channel + "_symbols"))


@pytest.mark.capture
def test_single_event_aba_return_and_observed_differences():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = {e["path"]: e for e in entries if "expected_event_decode" in e}
    ids = ("event-001-a", "event-001-b", "event-001-a-return")
    decoded = []
    for capture_id in ids:
        key = f"experiments/{capture_id}/capture.wav"
        if key not in records or not (root / key).exists():
            pytest.skip("Complete pinned event-001 A/B/A recording series required")
        entry = records[key]
        expected = entry["expected_event_decode"]
        artifact = decode_wav(root / key, expected["threshold"])
        assert artifact.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            symbols = getattr(artifact, channel + "_symbols")
            assert len(symbols) == expected[channel + "_symbol_count"]
            assert (
                hashlib.sha256(symbols.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
        decoded.append(artifact)
    first, changed, returned = decoded
    for channel, expected_changes in (("left", 88307), ("right", 1471718)):
        a, b, again = [getattr(v, channel + "_symbols") for v in (first, changed, returned)]
        assert len(a) == len(b) == 1970367
        assert len(again) == len(a) - 10
        assert np.array_equal(a[: len(again)], again)
        assert np.all(a[len(again) :] == 1)
        differences = np.flatnonzero(a != b)
        assert len(differences) == expected_changes
        assert differences[0] == 9309


@pytest.mark.capture
def test_step2_aba_control_and_independent_onset_spacing():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = {e["path"]: e for e in entries if "expected_event_decode" in e}
    captures = ("event-002-a", "event-002-b", "event-002-a-return", "event-001-a")
    decoded = []
    for capture_id in captures:
        key = f"experiments/{capture_id}/capture.wav"
        if key not in records or not (root / key).exists():
            pytest.skip("Pinned Step 2 A/B/A and Step 1 baseline required")
        entry = records[key]
        expected = entry["expected_event_decode"]
        artifact = decode_wav(root / key, expected["threshold"])
        assert artifact.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            symbols = getattr(artifact, channel + "_symbols")
            assert len(symbols) == expected[channel + "_symbol_count"]
            assert (
                hashlib.sha256(symbols.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
        decoded.append(artifact)
    for channel, count in (("left", 88122), ("right", 1471410)):
        a, b, again, old = [getattr(v, channel + "_symbols") for v in decoded]
        assert len(a) == len(again) == 1970367
        assert np.array_equal(a, again)
        assert np.array_equal(a, old)
        overlap = min(len(a), len(b))
        differences = np.flatnonzero(a[:overlap] != b[:overlap])
        assert len(differences) == count
        assert differences[0] == 9405
        if channel == "left":
            assert len(a) - len(b) == 1
            assert a[-1] == 1
        else:
            assert len(a) == len(b)


@pytest.mark.capture
def test_step3_return_control_and_falsified_symbol_prediction():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = {e["path"]: e for e in entries if "expected_event_decode" in e}
    captures = ("event-002-a", "event-003-b", "event-003-a-return")
    decoded = []
    for capture_id in captures:
        key = f"experiments/{capture_id}/capture.wav"
        if key not in records or not (root / key).exists():
            pytest.skip("Pinned Step 3 B/return and reused empty baseline required")
        entry = records[key]
        expected = entry["expected_event_decode"]
        a = decode_wav(root / key, expected["threshold"])
        assert a.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            values = getattr(a, channel + "_symbols")
            assert len(values) == expected[channel + "_symbol_count"]
            assert (
                hashlib.sha256(values.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
        decoded.append(a)
    for channel, observed in (("left", 9502), ("right", 9500)):
        baseline, changed, returned = [getattr(a, channel + "_symbols") for a in decoded]
        assert len(baseline) == len(returned) == 1970367
        assert np.array_equal(baseline, returned)
        n = min(len(baseline), len(changed))
        first_change = int(np.flatnonzero(baseline[:n] != changed[:n])[0])
        assert first_change == observed
        assert first_change != 9501  # Preserve failure of the preregistered exact prediction.
        assert first_change // 4 == 2375  # Post-observation packed-label location.


@pytest.mark.capture
def test_populated_state_repeat_matches_original_event():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    eligible = [e for e in entries if "expected_populated_repeat" in e]
    if not eligible:
        pytest.skip("Pinned populated-state repeat recording required")
    for entry in eligible:
        expected = entry["expected_populated_repeat"]
        path = root / entry["path"]
        reference = root / f"experiments/{expected['reference_id']}/capture.wav"
        if not path.exists() or not reference.exists():
            pytest.skip("Populated-state repeat or original event recording unavailable")
        actual = decode_wav(path, expected["threshold"])
        original = decode_wav(reference, expected["threshold"])
        assert actual.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            symbols = getattr(actual, channel + "_symbols")
            assert len(symbols) == expected["symbols_per_channel"]
            assert (
                hashlib.sha256(symbols.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
            assert np.array_equal(symbols, getattr(original, channel + "_symbols"))


@pytest.mark.capture
def test_joint_capture_content_and_step3_increment_tail():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = [e for e in entries if "expected_joint_decode" in e]
    if not records:
        pytest.skip("Pinned joint-state capture required")
    reference_path = root / "experiments/event-003-b/capture.wav"
    if not reference_path.exists():
        pytest.skip("Step 3 reference required")
    reference = decode_wav(reference_path, 0.0063)
    for entry in records:
        path = root / entry["path"]
        if not path.exists():
            pytest.skip("Joint-state capture required")
        expected = entry["expected_joint_decode"]
        joint = decode_wav(path, expected["threshold"])
        assert joint.metadata["source_sha256"] == entry["sha256"]
        for ch in ("left", "right"):
            values = getattr(joint, ch + "_symbols")
            assert len(values) == expected["symbols_per_channel"]
            assert hashlib.sha256(values.tobytes()).hexdigest() == expected[ch + "_symbols_sha256"]
            a, b = [
                phase_increments(staggered_phases(getattr(v, ch + "_symbols")))
                for v in (reference, joint)
            ]
            count = min(len(a), len(b))
            differences = np.flatnonzero(a[:count] != b[:count])
            assert len(differences) > 0
            assert int(differences[-1]) == 60010
            assert np.array_equal(a[60011:count], b[60011:count])


@pytest.mark.capture
def test_partial_tone_capture_and_observed_repeat():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = [e for e in entries if "expected_tone_decode" in e]
    if not records:
        pytest.skip("Pinned partial-tone capture required")
    for entry in records:
        path = root / entry["path"]
        if not path.exists():
            pytest.skip("Partial-tone recording unavailable")
        expected = entry["expected_tone_decode"]
        artifact = decode_wav(path, expected["threshold"])
        assert artifact.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            values = getattr(artifact, channel + "_symbols")
            assert len(values) == expected[channel + "_symbol_count"]
            assert (
                hashlib.sha256(values.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
            increments = phase_increments(staggered_phases(values))
            # Preserve observed periodic evidence; this does not identify tone/state bytes.
            assert smallest_period(increments[1179129:1181733], 2048) == 520


@pytest.mark.capture
def test_new_empty_baseline_repeat_including_partial_endpoints():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = [e for e in entries if "expected_empty_decode" in e]
    if len(records) != 2:
        pytest.skip("Pinned minimal-state baseline pair required")
    decoded = []
    for entry in records:
        path = root / entry["path"]
        if not path.exists():
            pytest.skip("Minimal-state recording unavailable")
        expected = entry["expected_empty_decode"]
        artifact = decode_wav(path, expected["threshold"])
        assert artifact.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            values = getattr(artifact, channel + "_symbols")
            assert len(values) == expected["symbols_per_channel"]
            assert (
                hashlib.sha256(values.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
            boundary = artifact.metadata["channels"][channel]["boundary_sign_intervals"][
                "incomplete_final_cycle_bits"
            ]
            assert boundary == expected["incomplete_final_sign_intervals"][channel]
        decoded.append(artifact)
    assert np.array_equal(decoded[0].left_symbols, decoded[1].left_symbols)
    assert np.array_equal(decoded[0].right_symbols, decoded[1].right_symbols)


@pytest.mark.capture
def test_minimal_one_tone_repeat_and_unchanged_prefix():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = [e for e in entries if "expected_minimal_tone_decode" in e]
    if len(records) != 2:
        pytest.skip("Pinned one-tone repeat pair required")
    baseline_path = root / "experiments/empty-001-a/capture.wav"
    if not baseline_path.exists():
        pytest.skip("Minimal empty baseline unavailable")
    baseline = decode_wav(baseline_path, 0.0063)
    decoded = []
    for entry in records:
        path = root / entry["path"]
        if not path.exists():
            pytest.skip("One-tone recording unavailable")
        expected = entry["expected_minimal_tone_decode"]
        a = decode_wav(path, expected["threshold"])
        assert a.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            values = getattr(a, channel + "_symbols")
            original = getattr(baseline, channel + "_symbols")
            assert len(values) == expected["symbols_per_channel"]
            assert (
                hashlib.sha256(values.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
            assert (
                a.metadata["channels"][channel]["boundary_sign_intervals"][
                    "incomplete_final_cycle_bits"
                ]
                == expected["incomplete_final_sign_intervals"][channel]
            )
            assert np.array_equal(values[:43354], original[:43354])
            assert values[43354] != original[43354]
        decoded.append(a)
    assert np.array_equal(decoded[0].left_symbols, decoded[1].left_symbols)
    assert np.array_equal(decoded[0].right_symbols, decoded[1].right_symbols)


@pytest.mark.capture
def test_copy_capture_and_shared_displaced_block():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = [e for e in entries if "expected_copy_decode" in e]
    reference_path = root / "experiments/empty-001-b-tone/capture.wav"
    if not records or not reference_path.exists():
        pytest.skip("Pinned copy/source captures required")
    reference = decode_wav(reference_path, 0.0063)
    for entry in records:
        path = root / entry["path"]
        if not path.exists():
            pytest.skip("Copy recording unavailable")
        expected = entry["expected_copy_decode"]
        copied = decode_wav(path, expected["threshold"])
        assert copied.metadata["source_sha256"] == entry["sha256"]
        for channel in ("left", "right"):
            values = getattr(copied, channel + "_symbols")
            before = getattr(reference, channel + "_symbols")
            assert len(values) == expected["symbols_per_channel"]
            assert (
                hashlib.sha256(values.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
            assert (
                copied.metadata["channels"][channel]["boundary_sign_intervals"][
                    "incomplete_final_cycle_bits"
                ]
                == expected["incomplete_final_sign_intervals"][channel]
            )
            changes = np.flatnonzero(values[: len(before)] != before)
            assert changes[0] == 43270
            a, b = [phase_increments(staggered_phases(x)) for x in (before, values)]
            assert np.array_equal(a[76819:177169], b[76735:177085])
            assert a[76818] != b[76734] and a[177169] != b[177085]


@pytest.mark.capture
def test_recovered_copy_capture_negative_acquisition_and_reference_anchors():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / "tests/fixtures/manifest.json").read_text())["captures"]
    records = [e for e in entries if "expected_recovered_copy_decode" in e]
    reference_path = root / "experiments/empty-001-c-copy-to-1/capture.wav"
    if not records or not reference_path.exists():
        pytest.skip("Pinned recovered-copy/reference captures required")
    reference = decode_wav(reference_path, 0.0063)
    for entry in records:
        path = root / entry["path"]
        if not path.exists():
            pytest.skip("Recovered-copy recording unavailable")
        expected = entry["expected_recovered_copy_decode"]
        actual = decode_wav(path, expected["threshold"])
        assert actual.metadata["source_sha256"] == entry["sha256"]
        assert actual.metadata["decoder_version"] == expected["decoder_version"]
        for channel in ("left", "right"):
            values = getattr(actual, channel + "_symbols")
            before = getattr(reference, channel + "_symbols")
            assert len(values) == expected["symbols_per_channel"]
            assert (
                hashlib.sha256(values.tobytes()).hexdigest()
                == expected[channel + "_symbols_sha256"]
            )
            meta = actual.metadata["channels"][channel]
            assert meta["initial_negative_origin_sample"] == 77528
            assert (
                meta["boundary_sign_intervals"]["incomplete_final_cycle_bits"]
                == expected["incomplete_final_sign_intervals"][channel]
            )
            differences = np.flatnonzero(values[: len(before)] != before)
            assert int(differences[0]) == (177093 if channel == "left" else 177092)
            a, b = [phase_increments(staggered_phases(x)) for x in (before, values)]
            for position in (90000, 120000, 150000):
                assert np.array_equal(a[position : position + 128], b[position : position + 128])
