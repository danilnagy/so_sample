/**
 * Device transfer in the browser: play a restore through the audio output, record a
 * backup from the audio input. The lessons of the research harness apply: silence before
 * and after the restore so no output buffer is cut, a constant level, no browser audio
 * processing on the input, and the recording stops by itself 1.5 s after the transfer.
 *
 * A backup is two different label streams, one per channel, so the input must be stereo.
 * Browsers record from the system default input unless a device is named, and a laptop's
 * built-in microphone is mono; the input is therefore chosen and checked before recording.
 */

import { type LabelStreams } from '../core/labels';
import { synthesizePcm16 } from '../core/modem/encode';
import { type WavData, floatToPcm16, wavFromPcm16 } from '../core/wav';

export const SEND_RATE = 44100;
const LEAD_SECONDS = 0.25;
const TAIL_SECONDS = 1.0;
/** Peak that counts as signal when recording (normalised). */
const SIGNAL_PEAK = 0.005;
const END_QUIET_SECONDS = 1.5;
const MAX_RECORD_SECONDS = 360;

export interface Transfer {
  /** Seconds of audio in the transfer. */
  seconds: number;
  /** Resolves when playback has finished or was cancelled. */
  done: Promise<void>;
  cancel: () => void;
  /** Seconds played so far. */
  position: () => number;
}

/** Play the restore for the given label streams at a software gain of 0..1. */
export function sendRestore(streams: LabelStreams, gain: number): Transfer {
  const { pcm } = synthesizePcm16(streams, { sampleRate: SEND_RATE });
  const frames = pcm.length / 2;
  const lead = Math.round(LEAD_SECONDS * SEND_RATE);
  const tail = Math.round(TAIL_SECONDS * SEND_RATE);
  const context = new AudioContext({ sampleRate: SEND_RATE });
  const buffer = context.createBuffer(2, lead + frames + tail, SEND_RATE);
  for (let c = 0; c < 2; c++) {
    const channel = buffer.getChannelData(c);
    for (let i = 0; i < frames; i++) channel[lead + i] = (pcm[2 * i + c] / 32768) * gain;
  }
  const source = context.createBufferSource();
  source.buffer = buffer;
  source.connect(context.destination);
  const started = context.currentTime + 0.1;
  let finished: () => void = () => {};
  const done = new Promise<void>((resolve) => (finished = resolve));
  source.onended = () => {
    finished();
    void context.close();
  };
  source.start(started);
  return {
    seconds: buffer.duration,
    done,
    cancel: () => source.stop(),
    position: () => Math.max(0, Math.min(buffer.duration, context.currentTime - started)),
  };
}

// Inputs

export interface AudioInput {
  /** The browser's device id; '' is the system default. */
  id: string;
  /** Blank until the page has been allowed to use an input once. */
  label: string;
}

export interface InputProbe {
  label: string;
  /** Channels the browser delivers from this input, or null when it does not say. */
  channelCount: number | null;
  sampleRate: number | null;
}

/** The input cannot carry a backup: it delivers one channel. */
export class MonoInputError extends Error {}

export function monoInputMessage(label: string): string {
  return `${label || 'This input'} is mono. A backup needs both channels: choose a stereo line input.`;
}

export function sameSignalMessage(label: string): string {
  return `${label || 'The input'} delivered the same signal on both channels, so it is a mono input even though the browser calls it stereo (a microphone jack or USB headset adapter does this). Use a true stereo line input, such as an audio interface.`;
}

/** Below this ratio of the channel difference to the channel level, the two channels are one signal. */
const SAME_SIGNAL_RATIO = 0.05;

/**
 * A backup carries different label streams on left and right, so a recording whose
 * channels are (nearly) the same cannot be one, whatever the browser said about the
 * input. Throws MonoInputError for such a recording.
 */
export function requireDistinctChannels(wav: WavData, label = ''): void {
  if (wav.channels.length < 2) throw new MonoInputError(monoInputMessage(label));
  const [left, right] = wav.channels;
  let level = 0;
  let difference = 0;
  for (let i = 0; i < left.length; i++) {
    level += left[i] * left[i] + right[i] * right[i];
    const d = left[i] - right[i];
    difference += d * d;
  }
  if (level > 0 && Math.sqrt(difference / level) < SAME_SIGNAL_RATIO) throw new MonoInputError(sameSignalMessage(label));
}

function inputConstraints(deviceId?: string): MediaTrackConstraints {
  return {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: { ideal: 2 },
    ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
  };
}

/** The audio inputs the browser offers, default first. */
export async function listInputs(): Promise<AudioInput[]> {
  const devices = await navigator.mediaDevices.enumerateDevices();
  return devices.filter((d) => d.kind === 'audioinput' && d.deviceId !== 'default').map((d) => ({ id: d.deviceId, label: d.label }));
}

/** Open an input once to learn its label and channel count, then release it. Unlocks device labels. */
export async function probeInput(deviceId?: string): Promise<InputProbe> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: inputConstraints(deviceId) });
  const track = stream.getAudioTracks()[0];
  const settings = track?.getSettings() ?? {};
  for (const t of stream.getTracks()) t.stop();
  return { label: track?.label ?? '', channelCount: settings.channelCount ?? null, sampleRate: settings.sampleRate ?? null };
}

/**
 * Assemble the worklet's blocks into a stereo recording. `channelCount` is the most
 * channels any block carried; one channel, or two channels carrying the same signal,
 * cannot hold a backup and is refused rather than passed on, which would only fail
 * later as a checksum error.
 */
export function assembleRecording(chunks: Float32Array[][], channelCount: number, frames: number, sampleRate: number, label = ''): WavData {
  if (channelCount < 2) throw new MonoInputError(monoInputMessage(label));
  const channels = [new Float64Array(frames), new Float64Array(frames)];
  let offset = 0;
  for (const chunk of chunks) {
    for (let c = 0; c < 2; c++) channels[c].set(chunk[Math.min(c, chunk.length - 1)], offset);
    offset += chunk[0].length;
  }
  const wav: WavData = { sampleRate, channels, bitsPerSample: 32, format: 'float' };
  requireDistinctChannels(wav, label);
  return wav;
}

/** A recording as a 16-bit stereo WAV, so a failed attempt can be kept and analysed. */
export function recordingWavBytes(wav: WavData): Uint8Array {
  const [left, right] = wav.channels;
  const interleaved = new Int16Array(left.length * 2);
  for (let i = 0; i < left.length; i++) {
    interleaved[2 * i] = floatToPcm16(Math.max(-1, Math.min(1, left[i])));
    interleaved[2 * i + 1] = floatToPcm16(Math.max(-1, Math.min(1, right[i])));
  }
  return wavFromPcm16(interleaved, 2, wav.sampleRate);
}

/** One line about a recording for a failure message: length and peak per channel. */
export function describeRecording(wav: WavData): string {
  const peak = (c: Float64Array) => {
    let m = 0;
    for (let i = 0; i < c.length; i++) m = Math.max(m, Math.abs(c[i]));
    return `${(m * 100).toFixed(1)}%`;
  };
  return `${(wav.channels[0].length / wav.sampleRate).toFixed(1)} s at ${wav.sampleRate} Hz, peak left ${peak(wav.channels[0])}, right ${peak(wav.channels[1])}`;
}

export interface Recording {
  /** Resolves with the recording once the transfer has ended, or null when cancelled; rejects when the input cannot carry one. */
  result: Promise<WavData | null>;
  cancel: () => void;
  /** Latest peak level (normalised) and whether signal has been seen. */
  status: () => { peak: number; started: boolean; seconds: number };
}

const WORKLET = `
class Tap extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input.length) this.port.postMessage(input.map((c) => c.slice()));
    return true;
  }
}
registerProcessor('sosample-tap', Tap);
`;

/**
 * Record from the given input (the system default when omitted) until the transfer has
 * been quiet for 1.5 s. Throws MonoInputError at once when the browser reports a
 * one-channel input.
 */
export async function recordBackup(deviceId?: string): Promise<Recording> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: inputConstraints(deviceId) });
  const track = stream.getAudioTracks()[0];
  const label = track?.label ?? '';
  if (track?.getSettings().channelCount === 1) {
    for (const t of stream.getTracks()) t.stop();
    throw new MonoInputError(monoInputMessage(label));
  }
  // A setup that fails part-way lets go of the input and the audio context, so the browser's recording indicator goes out.
  let context: AudioContext | null = null;
  let source: MediaStreamAudioSourceNode;
  let tap: AudioWorkletNode;
  try {
    context = new AudioContext();
    const url = URL.createObjectURL(new Blob([WORKLET], { type: 'application/javascript' }));
    try {
      await context.audioWorklet.addModule(url);
    } finally {
      URL.revokeObjectURL(url);
    }
    source = context.createMediaStreamSource(stream);
    tap = new AudioWorkletNode(context, 'sosample-tap', { numberOfInputs: 1, numberOfOutputs: 0 });
    source.connect(tap);
  } catch (error) {
    for (const t of stream.getTracks()) t.stop();
    void context?.close().catch(() => {});
    throw error;
  }
  const audio = context;
  const chunks: Float32Array[][] = [];
  let frames = 0;
  let peak = 0;
  let started = false;
  let quietFrames = 0;
  let channelCount = 0;
  let finish: (value: WavData | null) => void = () => {};
  let fail: (error: Error) => void = () => {};
  const result = new Promise<WavData | null>((resolve, reject) => {
    finish = resolve;
    fail = reject;
  });
  // Stops once: a cancel after the automatic stop finds nothing left to close.
  let stopped = false;
  const stop = (build: () => WavData | null) => {
    if (stopped) return;
    stopped = true;
    tap.port.onmessage = null;
    source.disconnect();
    for (const t of stream.getTracks()) t.stop();
    void audio.close().catch(() => {});
    try {
      finish(build());
    } catch (error) {
      fail(error as Error);
    }
  };
  const assemble = (): WavData => assembleRecording(chunks, channelCount, frames, audio.sampleRate, label);
  tap.port.onmessage = (event: MessageEvent<Float32Array[]>) => {
    const chunk = event.data;
    channelCount = Math.max(channelCount, chunk.length);
    chunks.push(chunk);
    frames += chunk[0].length;
    let blockPeak = 0;
    for (const channel of chunk) for (let i = 0; i < channel.length; i++) blockPeak = Math.max(blockPeak, Math.abs(channel[i]));
    peak = blockPeak;
    if (blockPeak >= SIGNAL_PEAK) {
      started = true;
      quietFrames = 0;
    } else if (started) {
      quietFrames += chunk[0].length;
      if (quietFrames >= END_QUIET_SECONDS * audio.sampleRate) stop(assemble);
    }
    if (frames >= MAX_RECORD_SECONDS * audio.sampleRate) stop(() => (started ? assemble() : null));
  };
  return {
    result,
    cancel: () => stop(() => null),
    status: () => ({ peak, started, seconds: frames / audio.sampleRate }),
  };
}
