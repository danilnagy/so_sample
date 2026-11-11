"""Play and record through an audio interface, keeping integer PCM untouched.

The sounddevice backend is optional: install it with ``pip install -e ".[hardware]"``.
Tests use ``ScriptedBackend``. Recordings are written exactly as the driver delivers
them; nothing is normalized, trimmed, resampled or converted to mono.
"""

import io
import queue
import time
from dataclasses import dataclass, field

import numpy as np
import soundfile as sf

SUBTYPE_DTYPES = {"PCM_16": "int16", "PCM_24": "int32"}
FULL_SCALE = {"int16": 32768.0, "int32": 2147483648.0}

# Established reduced-level backups peak near 0.15 with a noise floor near 0.001.
DEFAULT_SIGNAL_PEAK = 0.02
DEFAULT_END_QUIET_SECONDS = 1.5
DEFAULT_BLOCK_SECONDS = 0.05
LOW_PEAK_WARNING = 0.03
CLIP_PEAK_WARNING = 0.98
CHANNEL_RATIO_WARNING = 0.5


class HardwareUnavailable(RuntimeError):
    """The optional audio backend or a requested device is not available."""


def _sounddevice():
    try:
        import sounddevice
    except (ImportError, OSError) as exc:
        raise HardwareUnavailable(
            'Audio backend unavailable; install it with: pip install -e ".[hardware]"'
        ) from exc
    return sounddevice


def list_devices():
    sd = _sounddevice()
    hostapis = sd.query_hostapis()
    default_in, default_out = sd.default.device
    return [
        {
            "index": index,
            "name": info["name"],
            "hostapi": hostapis[info["hostapi"]]["name"],
            "max_input_channels": info["max_input_channels"],
            "max_output_channels": info["max_output_channels"],
            "default_samplerate": info["default_samplerate"],
            "default_high_output_latency": info["default_high_output_latency"],
            "default_input": index == default_in,
            "default_output": index == default_out,
        }
        for index, info in enumerate(sd.query_devices())
    ]


def resolve_device(spec, kind, hostapi=None, devices=None):
    """Find one device by index or case-insensitive name fragment with 2 channels."""
    devices = list_devices() if devices is None else devices
    key = "max_input_channels" if kind == "input" else "max_output_channels"
    if spec is None:
        matches = [d for d in devices if d[f"default_{kind}"]]
    elif isinstance(spec, int) or (isinstance(spec, str) and spec.isdigit()):
        matches = [d for d in devices if d["index"] == int(spec)]
    else:
        matches = [d for d in devices if spec.lower() in d["name"].lower()]
    if hostapi:
        matches = [d for d in matches if hostapi.lower() in d["hostapi"].lower()]
    matches = [d for d in matches if d[key] >= 2]
    if not matches:
        raise HardwareUnavailable(f"No stereo {kind} device matches {spec!r} (hostapi {hostapi!r})")
    if len(matches) > 1:
        names = "; ".join(f"{d['index']}: {d['name']} [{d['hostapi']}]" for d in matches)
        raise HardwareUnavailable(
            f"Several {kind} devices match {spec!r}; give an index or --hostapi: {names}"
        )
    return matches[0]


class _InputStream:
    def __init__(self, sd, device, rate, dtype, block_frames):
        self.blocks = queue.Queue()
        self.status_flags = []

        def callback(indata, frames, time_info, status):
            if status:
                self.status_flags.append(str(status))
            self.blocks.put(indata.copy())

        self.stream = sd.InputStream(
            samplerate=rate,
            channels=2,
            dtype=dtype,
            device=device,
            blocksize=block_frames,
            callback=callback,
        )

    def __enter__(self):
        self.stream.start()
        return self

    def __exit__(self, *exc):
        self.stream.stop()
        self.stream.close()

    def read(self):
        try:
            return self.blocks.get(timeout=5)
        except queue.Empty as exc:
            raise HardwareUnavailable("Audio input stopped delivering data") from exc


class SounddeviceBackend:
    def __init__(self, input_device=None, output_device=None, hostapi=None):
        self.sd = _sounddevice()
        devices = list_devices()
        self.input = resolve_device(input_device, "input", hostapi, devices)
        self.output = resolve_device(output_device, "output", hostapi, devices)

    def describe(self):
        return {
            "backend": "sounddevice",
            "input": {k: self.input[k] for k in ("index", "name", "hostapi")},
            "output": {k: self.output[k] for k in ("index", "name", "hostapi")},
        }

    def open_input(self, rate, dtype, block_frames):
        return _InputStream(self.sd, self.input["index"], rate, dtype, block_frames)

    def play(self, samples, rate):
        self.sd.play(samples, rate, device=self.output["index"], blocking=False)
        status = self.sd.wait()
        # Some host APIs (MME) can report completion before the device has played the
        # last buffers. Callers pad with silence; this wait is an extra margin.
        time.sleep(self.output.get("default_high_output_latency", 0.2) + 0.1)
        return [str(status)] if status else []

    def playrec(self, samples, rate, dtype):
        tail = np.zeros((rate, 2), dtype=samples.dtype)
        samples = np.concatenate([samples, tail])
        recorded = self.sd.playrec(
            samples,
            rate,
            channels=2,
            dtype=dtype,
            device=(self.input["index"], self.output["index"]),
            blocking=False,
        )
        status = self.sd.wait()
        return recorded, [str(status)] if status else []


@dataclass
class ScriptedBackend:
    """Test double: input blocks are served in order, then silence; playback is logged.

    ``streams`` gives one block list per opened input stream, so leftovers from one
    recording never leak into the next, as with a real interface.
    """

    input_blocks: list = field(default_factory=list)
    streams: list = field(default_factory=list)
    playrec_result: np.ndarray | None = None
    played: list = field(default_factory=list)
    status_flags: list = field(default_factory=list)

    def describe(self):
        return {"backend": "scripted", "input": None, "output": None}

    def open_input(self, rate, dtype, block_frames):
        backend = self

        source = backend.streams.pop(0) if backend.streams else backend.input_blocks

        class Stream:
            def __init__(self):
                self.status_flags = list(backend.status_flags)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return None

            def read(self):
                if source:
                    return source.pop(0)
                return np.zeros((block_frames, 2), dtype=dtype)

        return Stream()

    def play(self, samples, rate):
        self.played.append((samples, rate))
        return []

    def playrec(self, samples, rate, dtype):
        self.played.append((samples, rate))
        return self.playrec_result, []


@dataclass
class Recording:
    samples: np.ndarray
    rate: int
    subtype: str
    report: dict

    def wav_bytes(self):
        return wav_bytes(self.samples, self.rate, self.subtype)


def wav_bytes(samples, rate, subtype):
    if subtype not in SUBTYPE_DTYPES or samples.dtype != np.dtype(SUBTYPE_DTYPES[subtype]):
        raise ValueError("Recording dtype does not match the requested PCM subtype")
    output = io.BytesIO()
    sf.write(output, samples, rate, subtype=subtype, format="WAV")
    return output.getvalue()


ECHO_MIN_LAG_SECONDS = 0.0005
ECHO_MAX_LAG_SECONDS = 0.1
ECHO_COEFFICIENT_LIMIT = 0.05


def feedback_echo(samples, rate, start=None, seconds=4.0):
    """Look for a delayed copy of the recording inside itself, e.g. a monitoring loop.

    Clean backups correlate below about 0.015 at every tested lag. A loop through the
    PO-33 line input adds a delayed copy, which breaks phase decoding.
    """
    values = samples.astype(np.float64)
    length = round(seconds * rate)
    if start is None:
        start = max(0, (len(values) - length) // 2)
    segment = values[start : start + length]
    if len(segment) < rate // 2 or not np.all(segment.std(axis=0) > 0):
        return {"detected": False, "checked": False}
    low, high = round(ECHO_MIN_LAG_SECONDS * rate), round(ECHO_MAX_LAG_SECONDS * rate)
    size = 1 << int(np.ceil(np.log2(2 * len(segment))))
    spectra = [np.fft.rfft(segment[:, c] - segment[:, c].mean(), size) for c in (0, 1)]
    norms = [np.linalg.norm(segment[:, c] - segment[:, c].mean()) for c in (0, 1)]
    best = {"coefficient": 0.0}
    for a, b, name in (
        (0, 0, "left"),
        (1, 1, "right"),
        (0, 1, "left_from_right"),
        (1, 0, "right_from_left"),
    ):
        corr = np.fft.irfft(spectra[a] * np.conj(spectra[b]), size)[: high + 1]
        corr = corr / (norms[a] * norms[b])
        lag = low + int(np.argmax(np.abs(corr[low:])))
        if abs(corr[lag]) > abs(best["coefficient"]):
            best = {"coefficient": float(corr[lag]), "lag_ms": lag / rate * 1000, "channels": name}
    best["detected"] = abs(best["coefficient"]) >= ECHO_COEFFICIENT_LIMIT
    best["checked"] = True
    best["limit"] = ECHO_COEFFICIENT_LIMIT
    return best


def level_findings(peaks, status_flags, *, signal=True):
    findings = []
    if status_flags:
        findings.append(
            {
                "severity": "error",
                "message": "Driver reported input overflow or other stream problems; "
                "the recording may have gaps: " + ", ".join(sorted(set(status_flags))),
            }
        )
    if not signal:
        return findings
    if max(peaks) >= CLIP_PEAK_WARNING:
        findings.append(
            {"severity": "error", "message": "Peak near full scale; reduce the recording level"}
        )
    if min(peaks) < LOW_PEAK_WARNING:
        findings.append(
            {
                "severity": "warning",
                "message": "At least one channel is very quiet; check the stereo cable and level",
            }
        )
    if max(peaks) > 0 and min(peaks) / max(peaks) < CHANNEL_RATIO_WARNING:
        findings.append(
            {
                "severity": "warning",
                "message": "Left and right levels differ strongly; a mono cable or input is likely",
            }
        )
    return findings


def record_transfer(
    backend,
    rate=44100,
    subtype="PCM_16",
    *,
    signal_peak=DEFAULT_SIGNAL_PEAK,
    end_quiet_seconds=DEFAULT_END_QUIET_SECONDS,
    max_wait_seconds=120.0,
    max_seconds=900.0,
    block_seconds=DEFAULT_BLOCK_SECONDS,
    on_progress=None,
):
    """Record from now until a transfer has started and then stayed quiet.

    The whole recording is kept, including lead-in before the transfer and at least
    ``end_quiet_seconds`` of trailing quiet. Detection only decides when to stop.
    """
    dtype = SUBTYPE_DTYPES[subtype]
    scale = FULL_SCALE[dtype]
    block_frames = max(1, round(rate * block_seconds))
    blocks, frames = [], 0
    started_at = ended_at = None
    noise_peak = 0.0
    signal_peaks = np.zeros(2)
    quiet_frames = 0
    status = "max_duration"
    with backend.open_input(rate, dtype, block_frames) as stream:
        while True:
            block = stream.read()
            blocks.append(block)
            peaks = np.max(np.abs(block.astype(np.float64)), axis=0) / scale
            loud = bool(np.max(peaks) >= signal_peak)
            if started_at is None:
                if loud:
                    started_at = frames
                else:
                    noise_peak = max(noise_peak, float(np.max(peaks)))
            if started_at is not None:
                signal_peaks = np.maximum(signal_peaks, peaks)
                if loud:
                    quiet_frames, ended_at = 0, frames + len(block)
                else:
                    quiet_frames += len(block)
            frames += len(block)
            if on_progress:
                on_progress(
                    {
                        "seconds": frames / rate,
                        "signal": started_at is not None,
                        "peak": float(np.max(peaks)),
                    }
                )
            if started_at is None and frames >= max_wait_seconds * rate:
                status = "no_signal"
                break
            if started_at is not None and quiet_frames >= end_quiet_seconds * rate:
                status = "complete"
                break
            if frames >= max_seconds * rate:
                break
        flags = list(stream.status_flags)
    samples = np.concatenate(blocks)[:frames]
    peaks = [float(v) for v in signal_peaks]
    echo = {"detected": False, "checked": False}
    if started_at is not None and ended_at is not None:
        middle = (started_at + ended_at) // 2 - round(2 * rate)
        echo = feedback_echo(samples[started_at:ended_at], rate, max(0, middle - started_at))
    report = {
        "status": status,
        "sample_rate_hz": rate,
        "pcm_subtype": subtype,
        "frames": int(frames),
        "duration_seconds": frames / rate,
        "signal_start_seconds": None if started_at is None else started_at / rate,
        "signal_end_seconds": None if ended_at is None else ended_at / rate,
        "trailing_quiet_seconds": None if ended_at is None else (frames - ended_at) / rate,
        "noise_peak_before_signal": noise_peak,
        "signal_peaks_per_channel": peaks,
        "detection": {
            "signal_peak": signal_peak,
            "end_quiet_seconds": end_quiet_seconds,
            "block_seconds": block_frames / rate,
            "note": "Detection only chooses when to stop; the recording is not trimmed",
        },
        "stream_status_flags": flags,
        "feedback_echo": echo,
        "findings": level_findings(peaks, flags, signal=started_at is not None),
    }
    if echo["detected"]:
        report["findings"].append(
            {
                "severity": "error",
                "message": f"A delayed copy of the backup ({echo['lag_ms']:.1f} ms, "
                f"strength {abs(echo['coefficient']):.2f}) is mixed into the recording. "
                "Check that the computer output is unplugged from the PO-33 input",
            }
        )
    if status != "complete":
        report["findings"].append(
            {
                "severity": "error",
                "message": {
                    "no_signal": "No transfer signal arrived; check the cable and the "
                    "button combination",
                    "max_duration": "Transfer did not end within the time limit",
                }[status],
            }
        )
    return Recording(samples, rate, subtype, report)


def record_fixed(
    backend,
    seconds,
    rate=44100,
    subtype="PCM_16",
    *,
    wait_for_signal=False,
    signal_peak=DEFAULT_SIGNAL_PEAK,
    max_wait_seconds=60.0,
    on_progress=None,
):
    """Record ordinary audio such as pattern playback.

    With ``wait_for_signal`` the recording starts immediately (keeping the lead-in)
    and continues for ``seconds`` after the first block at or above ``signal_peak``.
    Otherwise it records exactly ``seconds`` from the start.
    """
    dtype = SUBTYPE_DTYPES[subtype]
    block_frames = max(1, round(rate * DEFAULT_BLOCK_SECONDS))
    scale = FULL_SCALE[dtype]
    target = None if wait_for_signal else round(seconds * rate)
    blocks, frames, onset, status = [], 0, None, "complete"
    with backend.open_input(rate, dtype, block_frames) as stream:
        while target is None or frames < target:
            block = stream.read()
            blocks.append(block)
            if onset is None and wait_for_signal:
                if np.max(np.abs(block.astype(np.float64))) / scale >= signal_peak:
                    onset = frames
                    target = frames + round(seconds * rate)
                elif frames + len(block) >= max_wait_seconds * rate:
                    status, target = "no_signal", frames + len(block)
            frames += len(block)
            if on_progress:
                on_progress(
                    {"seconds": frames / rate, "signal": onset is not None or not wait_for_signal}
                )
        flags = list(stream.status_flags)
    samples = np.concatenate(blocks)[:target]
    peaks = (np.max(np.abs(samples.astype(np.float64)), axis=0) / scale).tolist()
    report = {
        "status": status,
        "sample_rate_hz": rate,
        "pcm_subtype": subtype,
        "frames": len(samples),
        "duration_seconds": len(samples) / rate,
        "signal_onset_seconds": None if onset is None else onset / rate,
        "seconds_after_onset": seconds if wait_for_signal else None,
        "peaks_per_channel": peaks,
        "stream_status_flags": flags,
        "findings": level_findings(peaks, flags, signal=max(peaks) > LOW_PEAK_WARNING),
    }
    if status == "no_signal":
        report["findings"].append(
            {"severity": "error", "message": "No playback sound arrived while waiting"}
        )
    elif max(peaks) <= LOW_PEAK_WARNING:
        report["findings"].append(
            {"severity": "warning", "message": "Playback recording is nearly silent"}
        )
    return Recording(samples, rate, subtype, report)


PLAYBACK_SIGNAL_PEAK = 0.005
PLAYBACK_MIN_LEAD_SECONDS = 0.3
PLAYBACK_MAX_LEAD_SECONDS = 4.5
PLAYBACK_LEVEL_CHANGE_RATIO = 1.5


def playback_findings(samples, rate, onset_seconds):
    """Check an ordinary playback recording against the registered audio protocols.

    Frozen first-tone and timing methods need at least 0.3 s of silence before the
    first sound, the first sound within 5 s of the recording start, and one constant
    level. A first sound after 4.5 s, or a level that changes part-way, is an error.
    """
    if onset_seconds is None:
        return [{"severity": "error", "message": "No playback sound was detected"}]
    findings = []
    if onset_seconds < PLAYBACK_MIN_LEAD_SECONDS:
        findings.append(
            {
                "severity": "error",
                "message": f"Sound began {onset_seconds:.2f} s after recording started; "
                "leave about one second of silence before pressing PLAY",
            }
        )
    if onset_seconds > PLAYBACK_MAX_LEAD_SECONDS:
        findings.append(
            {
                "severity": "error",
                "message": f"First sound came {onset_seconds:.1f} s after recording started; "
                "press PLAY about one second after Enter",
            }
        )
    scale = FULL_SCALE.get(str(samples.dtype), 1.0)
    values = np.abs(samples.astype(np.float64)).max(axis=1) / scale
    window = max(1, round(0.5 * rate))
    after = values[round(onset_seconds * rate) :]
    peaks = np.array(
        [after[i : i + window].max() for i in range(0, len(after) - window + 1, window)]
    )
    noise = float(values[: max(1, round(0.25 * rate))].max())
    active = peaks[peaks > max(5 * noise, 0.002)]
    if len(active) >= 6:
        third = len(active) // 3
        early, late = np.median(active[:third]), np.median(active[-third:])
        ratio = float(max(early, late) / min(early, late))
        if ratio > PLAYBACK_LEVEL_CHANGE_RATIO:
            findings.append(
                {
                    "severity": "error",
                    "message": f"Playback level changed by {ratio:.1f}x during the recording; "
                    "keep the PO-33 and computer volumes fixed",
                }
            )
    return findings


def load_for_playback(path):
    """Read a WAV for playback without changing its integer samples."""
    info = sf.info(str(path))
    if info.channels != 2:
        raise ValueError("Restore playback requires a stereo WAV")
    dtype = "int16" if info.subtype == "PCM_16" else "float32"
    samples, rate = sf.read(str(path), dtype=dtype, always_2d=True)
    return samples, rate


PLAYBACK_LEAD_SECONDS = 0.25
PLAYBACK_TAIL_SECONDS = 1.0


def play_wav(backend, path, gain=1.0):
    """Play a WAV. ``gain`` below 1 scales it down in software; the file is unchanged.

    Playback is padded with silence before and after. Ending the output stream right
    at the file's end cut off the final transfer packet on an MME device (PO-33 ERR),
    while ordinary media players, which drain their buffers, restored the same file.
    """
    if not np.isfinite(gain) or not 0 < gain <= 1:
        raise ValueError("Playback gain must be in (0, 1]")
    samples, rate = load_for_playback(path)
    file_frames = len(samples)
    if gain != 1:
        scale = 32768.0 if samples.dtype == np.int16 else 1.0
        samples = (samples.astype(np.float32) / scale * gain).astype(np.float32)
    lead = np.zeros((round(PLAYBACK_LEAD_SECONDS * rate), 2), dtype=samples.dtype)
    tail = np.zeros((round(PLAYBACK_TAIL_SECONDS * rate), 2), dtype=samples.dtype)
    samples = np.concatenate([lead, samples, tail])
    started = time.monotonic()
    flags = backend.play(samples, rate)
    return {
        "gain": gain,
        "peak_after_gain": float(
            np.max(np.abs(samples.astype(np.float64)))
            / (32768.0 if samples.dtype == np.int16 else 1.0)
        ),
        "sample_rate_hz": rate,
        "frames": file_frames,
        "duration_seconds": file_frames / rate,
        "padding_seconds": [PLAYBACK_LEAD_SECONDS, PLAYBACK_TAIL_SECONDS],
        "wall_seconds": time.monotonic() - started,
        "stream_status_flags": flags,
    }
