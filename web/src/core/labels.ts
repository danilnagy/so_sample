/**
 * Phase labels and wire bytes.
 *
 * A transfer is two streams (left and right channel) of phase labels 0..3, one per
 * carrier cycle. Label n groups the high coordinate of cycle n+1 with the low coordinate
 * of cycle n into a phase 0..3 (staggered quadrature); consecutive phase differences are
 * two-bit wire values, two cells per byte, right channel before left. The device sends a
 * fixed 4095-byte preamble, then the packet frame (see packets.ts).
 */

import { concatBytes } from './bytes';

export const FRAME_START_BYTE = 4095;

/** Circular order under (H, L) -> (not L, H): 10 -> 11 -> 01 -> 00. */
const CIRCULAR_INDEX = [3, 2, 0, 1];
const LABEL_FROM_INDEX = [2, 3, 1, 0];
/** Wire value <-> phase increment (self-inverse). */
const INCREMENT_FROM_WIRE = [0, 3, 2, 1];

export interface LabelStreams {
  left: Uint8Array;
  right: Uint8Array;
}

export function staggeredPhases(symbols: Uint8Array): Uint8Array {
  if (symbols.length < 2) throw new Error('At least two labels are required');
  const out = new Uint8Array(symbols.length - 1);
  for (let n = 0; n < out.length; n++) {
    out[n] = CIRCULAR_INDEX[(symbols[n + 1] & 2) | (symbols[n] & 1)];
  }
  return out;
}

export function phaseIncrements(phases: Uint8Array): Uint8Array {
  if (phases.length < 2) throw new Error('At least two phases are required');
  const out = new Uint8Array(phases.length - 1);
  for (let n = 0; n < out.length; n++) out[n] = (phases[n + 1] - phases[n] + 4) & 3;
  return out;
}

/** Inverse of staggeredPhases, given the two boundary coordinates it drops. */
export function restoreLabels(phases: Uint8Array, initialHigh: number, finalLow: number): Uint8Array {
  if (!phases.length) throw new Error('Phases are required');
  const out = new Uint8Array(phases.length + 1);
  const first = LABEL_FROM_INDEX[phases[0]];
  out[0] = (initialHigh << 1) | (first & 1);
  for (let n = 1; n < phases.length; n++) {
    out[n] = (LABEL_FROM_INDEX[phases[n - 1]] & 2) | (LABEL_FROM_INDEX[phases[n]] & 1);
  }
  out[phases.length] = (LABEL_FROM_INDEX[phases[phases.length - 1]] & 2) | finalLow;
  return out;
}

/** All complete wire bytes carried by two label streams. */
export function wireBytes(streams: LabelStreams): Uint8Array {
  const left = phaseIncrements(staggeredPhases(streams.left));
  const right = phaseIncrements(staggeredPhases(streams.right));
  const count = Math.floor((Math.min(left.length, right.length) - 1) / 2) * 2;
  if (count <= 0) throw new Error('Insufficient phase increments for a wire byte');
  const out = new Uint8Array(count / 2);
  for (let i = 0; i < out.length; i++) {
    const a = 1 + 2 * i;
    out[i] =
      INCREMENT_FROM_WIRE[right[a]] |
      (INCREMENT_FROM_WIRE[left[a]] << 2) |
      (INCREMENT_FROM_WIRE[right[a + 1]] << 4) |
      (INCREMENT_FROM_WIRE[left[a + 1]] << 6);
  }
  return out;
}

/** The fixed bytes every device transfer sends before the frame. */
export function preambleBytes(): Uint8Array {
  const out = new Uint8Array(FRAME_START_BYTE);
  for (let i = 0; i < FRAME_START_BYTE - 4; i++) out[i] = (i + 1) & 0xff;
  out.set([0x4d, 0xb8, 0x16, 0x5d], FRAME_START_BYTE - 4);
  return out;
}

/**
 * Label streams for an encoded frame body: the preamble, the body, then `carrierCells`
 * cycles holding the final phase. This reproduces the streams the device accepted in
 * every verified restore.
 */
export function labelsForBody(encodedBody: Uint8Array, carrierCells = 128): LabelStreams {
  const wire = concatBytes([preambleBytes(), encodedBody]);
  const channel = (shift: number): Uint8Array => {
    const phases = new Uint8Array(2 + 2 * wire.length + carrierCells);
    let phase = 0;
    let index = 2;
    for (const byte of wire) {
      phase = (phase + INCREMENT_FROM_WIRE[(byte >> shift) & 3]) & 3;
      phases[index++] = phase;
      phase = (phase + INCREMENT_FROM_WIRE[(byte >> (shift + 4)) & 3]) & 3;
      phases[index++] = phase;
    }
    phases.fill(phase, index);
    return restoreLabels(phases, 1, LABEL_FROM_INDEX[phase] & 1);
  };
  return { left: channel(2), right: channel(0) };
}
