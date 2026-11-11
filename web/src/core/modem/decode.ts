/**
 * Phase-label recovery from a recorded backup, by thresholded zero crossings.
 *
 * Crossings of the waveform are interpolated, their spacing rounded to quarter cycles of
 * a nominal 7800 Hz carrier, and the sign runs expanded to quarter bits. Acquisition
 * takes the first "11" pair; from there every carrier cycle's first two sign bits form
 * the label. When a frame does not decode, up to three repeated leading carrier labels
 * are dropped from one channel (a slipped leading label was seen on 2026-10-10), and
 * failing that the preamble is searched for in each channel: noise above the threshold
 * before the transfer makes the first crossing a false start, which shifts both the
 * grouping of the bits into labels and the frame start (seen in a browser recording on
 * 2026-11-07).
 */

import { type LabelStreams, labelsForBody, phaseIncrements, staggeredPhases } from '../labels';
import { type Frame, decodeLabels } from '../packets';
import type { WavData } from '../wav';

export const ESTABLISHED_THRESHOLD = 0.0063;
export const NOMINAL_CARRIER_HZ = 7800;
const MAX_LEADING_LABELS = 3;
/** Increments of the preamble compared when searching for it: 128 wire bytes. */
const PREAMBLE_NEEDLE = 256;

export class DecodeFailure extends Error {}

function roundHalfEven(x: number): number {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
}

/**
 * The quarter-cycle sign bits of one channel from acquisition on, starting with the
 * reinserted "1". A silence of over a second cannot occur inside a transfer, so the bits
 * are cut there and the longest run is kept: a click before the transfer is not it.
 */
export function decodeChannelBits(values: Float64Array, sampleRate: number, threshold: number): Uint8Array {
  // Typed arrays throughout: a four-minute backup has twelve million significant samples
  // and eight million bits per channel, which plain arrays made slow to build and collect.
  const n = values.length;
  let significant = 0;
  for (let i = 0; i < n; i++) if (Math.abs(values[i]) >= threshold) significant++;
  if (significant < 2) throw new DecodeFailure('No signal above the threshold');
  // Crossings between successive significant samples of opposite sign, with the sign reached.
  const crossings = new Float64Array(significant + 1);
  const sides = new Uint8Array(significant + 1);
  let count = 0;
  let previous = -1;
  let previousSign = false;
  for (let i = 0; i < n; i++) {
    const v = values[i];
    if (Math.abs(v) < threshold) continue;
    const sign = v >= 0;
    if (previous < 0) {
      if (!sign) {
        // Approximate the initial negative transition at the first significant sample.
        crossings[count] = i;
        sides[count++] = 0;
      }
    } else if (sign !== previousSign) {
      const a = Math.abs(values[previous]);
      crossings[count] = previous + (a / (a + Math.abs(v))) * (i - previous);
      sides[count++] = sign ? 1 : 0;
    }
    previous = i;
    previousSign = sign;
  }
  if (count < 2) throw new DecodeFailure('Insufficient zero crossings');
  const unit = sampleRate / (NOMINAL_CARRIER_HZ * 4);
  // Quarter-cycle counts per crossing interval; a gap over a second ends a run, and the longest run is kept.
  const counts = new Int32Array(count - 1);
  let runStart = 0;
  let runBits = 0;
  let bestStart = 0;
  let bestEnd = 0;
  let bestBits = 0;
  for (let k = 0; k + 1 < count; k++) {
    const c = roundHalfEven((crossings[k + 1] - crossings[k]) / unit);
    if (c > NOMINAL_CARRIER_HZ * 4) {
      if (runBits > bestBits) [bestStart, bestEnd, bestBits] = [runStart, k, runBits];
      runStart = k + 1;
      runBits = 0;
      counts[k] = 0;
      continue;
    }
    counts[k] = c;
    runBits += c;
  }
  if (runBits > bestBits) [bestStart, bestEnd, bestBits] = [runStart, count - 1, runBits];
  const bits = new Uint8Array(bestBits);
  let filled = 0;
  for (let k = bestStart; k < bestEnd; k++) {
    const bit = sides[k + 1] ? 0 : 1;
    const c = counts[k];
    if (bit) bits.fill(1, filled, filled + c);
    filled += c;
  }
  let sync = -1;
  for (let i = 0; i + 1 < bits.length; i++) {
    if (bits[i] === 1 && bits[i + 1] === 1) {
      sync = i;
      break;
    }
  }
  if (sync < 0) throw new DecodeFailure('No acquisition candidate');
  const out = new Uint8Array(bits.length - sync - 1);
  out[0] = 1;
  out.set(bits.subarray(sync + 2), 1);
  return out;
}

/** Labels from quarter-cycle bits: each cycle's first two bits, grouped from `offset`. */
export function labelsFromBits(bits: ArrayLike<number>, offset = 0): Uint8Array {
  const complete = Math.floor((bits.length - offset) / 4);
  if (complete <= 0) throw new DecodeFailure('No complete carrier cycles after acquisition');
  const symbols = new Uint8Array(complete);
  for (let g = 0; g < complete; g++) symbols[g] = (bits[offset + 4 * g] << 1) | bits[offset + 4 * g + 1];
  return symbols;
}

export function decodeChannel(values: Float64Array, sampleRate: number, threshold: number): Uint8Array {
  return labelsFromBits(decodeChannelBits(values, sampleRate, threshold));
}

export interface BitStreams {
  left: Uint8Array;
  right: Uint8Array;
}

export function decodeCaptureBits(wav: WavData, threshold = ESTABLISHED_THRESHOLD): BitStreams {
  if (wav.channels.length !== 2) throw new DecodeFailure(`Expected a stereo recording, found ${wav.channels.length} channels`);
  if (wav.sampleRate < 2 * NOMINAL_CARRIER_HZ) throw new DecodeFailure('Sample rate is too low for the carrier');
  const decode = (name: string, values: Float64Array): Uint8Array => {
    try {
      return decodeChannelBits(values, wav.sampleRate, threshold);
    } catch (error) {
      throw new DecodeFailure(`${name}: ${(error as Error).message}`);
    }
  };
  return { left: decode('left', wav.channels[0]), right: decode('right', wav.channels[1]) };
}

export function decodeCapture(wav: WavData, threshold = ESTABLISHED_THRESHOLD): LabelStreams {
  const bits = decodeCaptureBits(wav, threshold);
  return { left: labelsFromBits(bits.left), right: labelsFromBits(bits.right) };
}

let needles: LabelStreams | null = null;

/** The first increments of each channel's preamble, from the streams the device accepts. */
function preambleNeedles(): LabelStreams {
  if (!needles) {
    const clean = labelsForBody(new Uint8Array(0), 0);
    const increments = (labels: Uint8Array): Uint8Array => phaseIncrements(staggeredPhases(labels)).slice(1, 1 + PREAMBLE_NEEDLE);
    needles = { left: increments(clean.left), right: increments(clean.right) };
  }
  return needles;
}

/** Index of the first increment of the preamble in a label stream, or -1. */
function findPreamble(labels: Uint8Array, needle: Uint8Array): number {
  if (labels.length < needle.length + 2) return -1;
  const increments = phaseIncrements(staggeredPhases(labels));
  outer: for (let k = 0; k + needle.length <= increments.length; k++) {
    for (let j = 0; j < needle.length; j++) if (increments[k + j] !== needle[j]) continue outer;
    return k;
  }
  return -1;
}

export interface Alignment {
  streams: LabelStreams;
  /** Labels discarded before the preamble in each channel. */
  dropped: { left: number; right: number };
  /** Quarter-cycle grouping offset that produced each channel's labels. */
  offsets: { left: number; right: number };
}

/**
 * Find the preamble in each channel, trying the four groupings of the bits into labels,
 * and drop whatever precedes it. Returns null when a channel does not contain it.
 */
export function alignToPreamble(bits: BitStreams): Alignment | null {
  const needle = preambleNeedles();
  const channel = (b: Uint8Array, n: Uint8Array): { labels: Uint8Array; dropped: number; offset: number } | null => {
    for (let offset = 0; offset < 4; offset++) {
      let labels: Uint8Array;
      try {
        labels = labelsFromBits(b, offset);
      } catch {
        return null;
      }
      const k = findPreamble(labels, n);
      if (k < 0) continue;
      if (k >= 1) return { labels: labels.subarray(k - 1), dropped: k - 1, offset };
      // The leading carrier label is missing: stand one in so the increments line up.
      const padded = new Uint8Array(labels.length + 1);
      padded[0] = labels[0];
      padded.set(labels, 1);
      return { labels: padded, dropped: 0, offset };
    }
    return null;
  };
  const left = channel(bits.left, needle.left);
  const right = channel(bits.right, needle.right);
  if (!left || !right) return null;
  return {
    streams: { left: left.labels, right: right.labels },
    dropped: { left: left.dropped, right: right.dropped },
    offsets: { left: left.offset, right: right.offset },
  };
}

export interface FrameAttempt {
  method: string;
  passed: boolean;
  error?: string;
}

export interface RecoveredFrame {
  frame: Frame;
  streams: LabelStreams;
  attempts: FrameAttempt[];
}

function tryFrame(streams: LabelStreams): Frame | string {
  try {
    return decodeLabels(streams);
  } catch (error) {
    return (error as Error).message;
  }
}

/** Decode a recording to a frame, trying the fallbacks in turn; throws with all attempts. */
export function recoverFrame(wav: WavData, threshold = ESTABLISHED_THRESHOLD): RecoveredFrame {
  const attempts: FrameAttempt[] = [];
  const bits = decodeCaptureBits(wav, threshold);
  const streams: LabelStreams = { left: labelsFromBits(bits.left), right: labelsFromBits(bits.right) };
  const direct = tryFrame(streams);
  if (typeof direct !== 'string') {
    attempts.push({ method: 'crossing', passed: true });
    return { frame: direct, streams, attempts };
  }
  attempts.push({ method: 'crossing', passed: false, error: direct });
  for (const channel of ['left', 'right'] as const) {
    const labels = streams[channel];
    for (let drop = 1; drop <= MAX_LEADING_LABELS; drop++) {
      if (labels.length <= drop) break;
      let repeated = true;
      for (let i = 0; i <= drop; i++) if (labels[i] !== labels[0]) repeated = false;
      if (!repeated) break;
      const candidate: LabelStreams = { ...streams, [channel]: labels.subarray(drop) };
      const result = tryFrame(candidate);
      const method = `realigned ${channel} -${drop}`;
      if (typeof result !== 'string') {
        attempts.push({ method, passed: true });
        return { frame: result, streams: candidate, attempts };
      }
      attempts.push({ method, passed: false, error: result });
    }
  }
  const aligned = alignToPreamble(bits);
  if (!aligned) {
    attempts.push({ method: 'preamble search', passed: false, error: 'Preamble not found in both channels' });
  } else {
    const method = `preamble found after ${aligned.dropped.left} left and ${aligned.dropped.right} right labels`;
    const result = tryFrame(aligned.streams);
    if (typeof result !== 'string') {
      attempts.push({ method, passed: true });
      return { frame: result, streams: aligned.streams, attempts };
    }
    attempts.push({ method, passed: false, error: result });
  }
  throw new DecodeFailure(attempts.map((a) => `${a.method}: ${a.error}`).join('; '));
}
