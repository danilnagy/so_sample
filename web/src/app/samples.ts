/** Sample import (any audio file to native codes) and preview playback. */

import { readMulawWav } from '../core/archive';
import { SAMPLE_RATE, decodeMulawCodes, encodeMulaw } from '../core/mulaw';
import { toNativeRate } from '../core/resample';
import { parseWav } from '../core/wav';

export interface DecodedAudio {
  channels: Float64Array[];
  sampleRate: number;
}

async function decodeFile(bytes: Uint8Array): Promise<DecodedAudio> {
  try {
    const wav = parseWav(bytes);
    return { channels: wav.channels, sampleRate: wav.sampleRate };
  } catch {
    // Not an integer/float PCM WAV: let the browser decode it (mp3, ogg, flac, aiff...).
    const context = new OfflineAudioContext(1, 1, 48000);
    const buffer = await context.decodeAudioData(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer);
    const channels = Array.from({ length: buffer.numberOfChannels }, (_, c) => Float64Array.from(buffer.getChannelData(c)));
    return { channels, sampleRate: buffer.sampleRate };
  }
}

export function mixToMono(channels: Float64Array[]): Float64Array {
  if (channels.length === 1) return channels[0];
  const out = new Float64Array(channels[0].length);
  for (const channel of channels) for (let i = 0; i < out.length; i++) out[i] += channel[i] / channels.length;
  return out;
}

function nativeMulaw(bytes: Uint8Array): Uint8Array | null {
  try {
    const { codes, rate } = readMulawWav(bytes);
    return Math.abs(rate - SAMPLE_RATE) <= 1 ? codes : null;
  } catch {
    return null;
  }
}

/** Native codes for an audio file: mono mixdown, resampled to 23437.5 Hz, clipped, mu-law. */
export async function importAudioFile(file: File): Promise<{ codes: Uint8Array; sourceRate: number }> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  // A sample saved by this app (an archive's mu-law WAV at the device's rate) is its codes already: read exactly, not
  // decoded, resampled and encoded again.
  const exact = nativeMulaw(bytes);
  if (exact) return { codes: exact, sourceRate: SAMPLE_RATE };
  const audio = await decodeFile(bytes);
  const mono = mixToMono(audio.channels);
  const native = audio.sampleRate === SAMPLE_RATE ? mono : toNativeRate(mono, Math.round(audio.sampleRate));
  for (let i = 0; i < native.length; i++) native[i] = Math.max(-1, Math.min(1, native[i]));
  return { codes: encodeMulaw(native), sourceRate: audio.sampleRate };
}

let context: AudioContext | null = null;
let current: AudioBufferSourceNode | null = null;

/** The one audio context the app plays through, created on first use and resumed when the browser suspended it. */
export function audioContext(): AudioContext {
  context ??= new AudioContext();
  if (context.state === 'suspended') void context.resume();
  return context;
}

/**
 * iPhones and iPads mute Web Audio while the ring/silent switch is on silent, but not an
 * HTML media element that is playing. Playing a looped, silent clip through one during the
 * first tap puts the page's audio session in playback mode, and the preview then sounds
 * with the switch in either position. The element also wakes the context on that tap,
 * which browsers require before any sound. Installed once; harmless elsewhere.
 */
export function unlockAudioOnFirstGesture(): void {
  if (typeof document === 'undefined' || unlockInstalled) return;
  unlockInstalled = true;
  const unlock = () => {
    document.removeEventListener('pointerdown', unlock, true);
    document.removeEventListener('keydown', unlock, true);
    // Only Apple's touch devices need this; elsewhere the context is made on the first play, as before.
    if (!/iPad|iPhone|iPod/.test(navigator.userAgent) && !(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) return;
    audioContext();
    const keepAlive = document.createElement('audio');
    keepAlive.setAttribute('playsinline', '');
    keepAlive.loop = true;
    keepAlive.volume = 0.01;
    keepAlive.src = SILENT_WAV;
    keepAlive.hidden = true;
    document.body.appendChild(keepAlive);
    keepAlive.play().catch(() => {});
    silentPlayer = keepAlive;
  };
  document.addEventListener('pointerdown', unlock, true);
  document.addEventListener('keydown', unlock, true);
}

let unlockInstalled = false;
/** Kept referenced so the element is not collected while it loops. */
let silentPlayer: HTMLAudioElement | null = null;
export const silentPlayerForTests = (): HTMLAudioElement | null => silentPlayer;

/** A tenth of a second of silence as a 16-bit mono WAV at 8 kHz, small enough to inline. */
const SILENT_WAV = (() => {
  const samples = 800;
  const bytes = new Uint8Array(44 + samples * 2);
  const view = new DataView(bytes.buffer);
  const ascii = (at: number, text: string) => {
    for (let i = 0; i < text.length; i++) bytes[at + i] = text.charCodeAt(i);
  };
  ascii(0, 'RIFF');
  view.setUint32(4, 36 + samples * 2, true);
  ascii(8, 'WAVE');
  ascii(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, 8000, true);
  view.setUint32(28, 16000, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  ascii(36, 'data');
  view.setUint32(40, samples * 2, true);
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return `data:audio/wav;base64,${typeof btoa === 'function' ? btoa(binary) : ''}`;
})();

export interface Playback {
  /** The code index now playing, within the codes given, or null once playback has ended or was replaced. */
  position(): number | null;
}

const silent: Playback = { position: () => null };

/** Play a window of native codes at the device rate, times `rate` (2 is an octave up). */
export function playCodes(codes: Uint8Array, start = 0, end = codes.length, rate = 1): Playback {
  context = audioContext();
  current?.stop();
  const samples = decodeMulawCodes(codes.subarray(start, end));
  if (!samples.length) return silent;
  const buffer = context.createBuffer(1, samples.length, SAMPLE_RATE);
  buffer.getChannelData(0).set(Float32Array.from(samples));
  const source = context.createBufferSource();
  source.buffer = buffer;
  source.playbackRate.value = rate;
  source.connect(context.destination);
  source.start();
  current = source;
  const audio = context;
  const startedAt = audio.currentTime;
  // Only the length is kept: the decoded buffer can go once it is copied into the AudioBuffer.
  const length = samples.length;
  let ended = false;
  source.onended = () => (ended = true);
  return {
    position: () => {
      if (ended || current !== source) return null;
      const elapsed = (audio.currentTime - startedAt) * SAMPLE_RATE * rate;
      return elapsed >= length ? null : start + elapsed;
    },
  };
}

export function stopPreview(): void {
  current?.stop();
  current = null;
}

export function secondsOf(codes: number): string {
  return `${(codes / SAMPLE_RATE).toFixed(2)} s`;
}
