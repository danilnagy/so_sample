/**
 * Staggered-quadrature synthesis of a restore WAV from label streams.
 *
 * Two quadrature components switch sign at their zero crossings: I takes the following
 * label's high coordinate at 3/8 cycle, Q the current label's low coordinate at 1/8
 * cycle. A half-cycle primer (one low quarter, one high quarter) precedes the labels and
 * the final phase is held for half a cycle. 0.1 s of silence pads each end. The arithmetic
 * follows the Python encoder operation for operation so the output is byte-identical to
 * the restores the device accepted.
 */

import type { LabelStreams } from '../labels';
import { floatToPcm16, wavFromPcm16 } from '../wav';

export const DEFAULT_CARRIER_HZ = 7812.5;
export const DEFAULT_AMPLITUDE = 0.5;

export interface EncodeOptions {
  sampleRate?: 44100 | 48000;
  amplitude?: number;
  carrierHz?: number;
}

export function activeFrameCount(labelCount: number, sampleRate: number, carrierHz: number): number {
  return Math.ceil(((labelCount + 1) * sampleRate) / carrierHz);
}

/** Interleaved stereo PCM16 of the transfer, including the silence padding. */
export function synthesizePcm16(streams: LabelStreams, options: EncodeOptions = {}): { pcm: Int16Array; sampleRate: number } {
  const sampleRate = options.sampleRate ?? 44100;
  const amplitude = options.amplitude ?? DEFAULT_AMPLITUDE;
  const carrierHz = options.carrierHz ?? DEFAULT_CARRIER_HZ;
  if (sampleRate !== 44100 && sampleRate !== 48000) throw new Error('Sample rate must be 44100 or 48000');
  if (!(amplitude > 0 && amplitude <= 0.9)) throw new Error('Amplitude must be in (0, 0.9]');
  const count = streams.left.length;
  if (!count || count !== streams.right.length) throw new Error('Equal nonempty label streams are required');
  for (const [name, labels] of [['left', streams.left], ['right', streams.right]] as const) {
    if (labels[0] !== 2 && labels[0] !== 3) throw new Error(`${name}: the first label must start high`);
  }
  const active = activeFrameCount(count, sampleRate, carrierHz);
  const silence = Math.round(0.1 * sampleRate);
  const pcm = new Int16Array(2 * (active + 2 * silence));
  const scale = amplitude / Math.sqrt(2);
  const twoPi = 2 * Math.PI;
  const last = count - 1;
  const channel = (labels: Uint8Array, offset: number): void => {
    for (let n = 0; n < active; n++) {
      const cycles = (n * carrierHz) / sampleRate - 0.5;
      let value: number;
      if (cycles < -0.25) value = -amplitude;
      else if (cycles < 0) value = amplitude;
      else {
        const iIndex = Math.min(Math.max(Math.floor(cycles + 0.625), 0), last);
        const qIndex = Math.min(Math.max(Math.floor(cycles - 0.125), 0), last);
        const iSign = (labels[iIndex] >> 1) * 2 - 1;
        const qSign = (labels[qIndex] & 1) * 2 - 1;
        value = scale * (iSign * Math.cos(twoPi * (cycles - 0.125)) + qSign * Math.cos(twoPi * (cycles - 0.375)));
      }
      pcm[2 * (silence + n) + offset] = floatToPcm16(value);
    }
  };
  channel(streams.left, 0);
  channel(streams.right, 1);
  return { pcm, sampleRate };
}

export function encodeRestoreWav(streams: LabelStreams, options: EncodeOptions = {}): Uint8Array {
  const { pcm, sampleRate } = synthesizePcm16(streams, options);
  return wavFromPcm16(pcm, 2, sampleRate);
}

/** Seconds a transfer of `labelCount` labels takes at the device's carrier. */
export function transferSeconds(labelCount: number, carrierHz = DEFAULT_CARRIER_HZ): number {
  return (labelCount + 1) / carrierHz + 0.2;
}
