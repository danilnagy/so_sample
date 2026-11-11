/**
 * The second global record: bytes 0-127 the pattern chain (pattern - 1 each), byte 128
 * the chain length, byte 129 tempo 60-240, byte 130 swing 0-18. Bytes 131-146 are stored
 * per pattern with no audible effect; bytes from 147 and the whole first record are
 * filler the device writes. Everything not listed here is left as the template has it.
 */

export const CHAIN_LENGTH_OFFSET = 128;
export const TEMPO_OFFSET = 129;
export const SWING_OFFSET = 130;
export const MAX_CHAIN = 128;
export const TEMPO_RANGE = [60, 240] as const;
export const SWING_RANGE = [0, 18] as const;

export function readChain(second: Uint8Array): number[] {
  const length = second[CHAIN_LENGTH_OFFSET];
  if (length < 1 || length > MAX_CHAIN) throw new Error(`Unexpected chain length ${length}`);
  const chain: number[] = [];
  for (let i = 0; i < length; i++) {
    if (second[i] > 15) throw new Error(`Unexpected chain entry ${second[i]}`);
    chain.push(second[i] + 1);
  }
  return chain;
}

/** Writes the chain; entries past the length keep their old values, as the device does. */
export function writeChain(second: Uint8Array, chain: number[]): void {
  if (chain.length < 1 || chain.length > MAX_CHAIN) throw new Error('Chain must hold 1..128 patterns');
  chain.forEach((p, i) => {
    if (!Number.isInteger(p) || p < 1 || p > 16) throw new Error('Chain entries must be patterns 1..16');
    second[i] = p - 1;
  });
  second[CHAIN_LENGTH_OFFSET] = chain.length;
}

export function readTempo(second: Uint8Array): number {
  return second[TEMPO_OFFSET];
}

export function writeTempo(second: Uint8Array, bpm: number): void {
  if (!Number.isInteger(bpm) || bpm < TEMPO_RANGE[0] || bpm > TEMPO_RANGE[1]) throw new Error('Tempo must be 60..240');
  second[TEMPO_OFFSET] = bpm;
}

export function readSwing(second: Uint8Array): number {
  return second[SWING_OFFSET];
}

export function writeSwing(second: Uint8Array, swing: number): void {
  if (!Number.isInteger(swing) || swing < SWING_RANGE[0] || swing > SWING_RANGE[1]) throw new Error('Swing must be 0..18');
  second[SWING_OFFSET] = swing;
}
