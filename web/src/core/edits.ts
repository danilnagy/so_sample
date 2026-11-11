/**
 * Non-destructive sample modifications: a trim, a simple compressor, gain, normalisation
 * and fades, stored next to the original codes and applied when a project is compiled or
 * previewed. "Resample" bakes them into new codes.
 */

import { SAMPLE_RATE, decodeMulawCodes, encodeMulaw } from './mulaw';

export interface Compressor {
  /** dB below full scale at which gain reduction starts, -60..0. */
  thresholdDb: number;
  /** 1..20 */
  ratio: number;
  /** 0..24 dB */
  makeupDb: number;
}

export interface Modifications {
  /** Trim in codes of the original, start inclusive, end exclusive. */
  start: number;
  end: number;
  /** -24..24 dB */
  gainDb: number;
  /** Scale the result so its peak reaches full scale. */
  normalize: boolean;
  /** Fade lengths in codes. */
  fadeIn: number;
  fadeOut: number;
  compressor: Compressor | null;
}

export function noModifications(length: number): Modifications {
  return { start: 0, end: length, gainDb: 0, normalize: false, fadeIn: 0, fadeOut: 0, compressor: null };
}

export function isUnmodified(m: Modifications | undefined, length: number): boolean {
  return !m || (m.start === 0 && m.end === length && m.gainDb === 0 && !m.normalize && !m.fadeIn && !m.fadeOut && !m.compressor);
}

export function modifiedLength(m: Modifications | undefined, length: number): number {
  return m ? m.end - m.start : length;
}

const dbToGain = (db: number): number => 10 ** (db / 20);

/** Feed-forward compressor on a peak envelope (5 ms attack, 50 ms release). */
export function compress(samples: Float64Array, c: Compressor): void {
  const attack = Math.exp(-1 / (0.005 * SAMPLE_RATE));
  const release = Math.exp(-1 / (0.05 * SAMPLE_RATE));
  const threshold = dbToGain(c.thresholdDb);
  const slope = 1 - 1 / c.ratio;
  const makeup = dbToGain(c.makeupDb);
  let envelope = 0;
  for (let i = 0; i < samples.length; i++) {
    const level = Math.abs(samples[i]);
    envelope = level > envelope ? attack * envelope + (1 - attack) * level : release * envelope + (1 - release) * level;
    let gain = makeup;
    if (envelope > threshold) gain *= (envelope / threshold) ** -slope;
    samples[i] *= gain;
  }
}

/** The modified sample as floats in [-1, 1]. */
export function renderModifications(codes: Uint8Array, m: Modifications): Float64Array {
  const start = Math.max(0, Math.min(m.start, codes.length));
  const end = Math.max(start, Math.min(m.end, codes.length));
  const samples = decodeMulawCodes(codes.subarray(start, end));
  if (m.compressor) compress(samples, m.compressor);
  let gain = dbToGain(m.gainDb);
  if (m.normalize) {
    let peak = 0;
    for (let i = 0; i < samples.length; i++) peak = Math.max(peak, Math.abs(samples[i]) * gain);
    if (peak > 0) gain /= peak;
  }
  const fadeIn = Math.min(m.fadeIn, samples.length);
  const fadeOut = Math.min(m.fadeOut, samples.length);
  for (let i = 0; i < samples.length; i++) {
    let v = samples[i] * gain;
    if (i < fadeIn) v *= i / fadeIn;
    if (i >= samples.length - fadeOut) v *= (samples.length - 1 - i) / fadeOut;
    samples[i] = v > 1 ? 1 : v < -1 ? -1 : v;
  }
  return samples;
}

export function applyModifications(codes: Uint8Array, m: Modifications | undefined): Uint8Array {
  if (isUnmodified(m, codes.length)) return codes;
  return encodeMulaw(renderModifications(codes, m!));
}
