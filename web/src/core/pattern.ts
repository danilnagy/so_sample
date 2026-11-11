/**
 * One 1032-byte pattern: 16 steps x 16 sounds x 3 primary bytes, 256 auxiliary bytes,
 * 8 footer bytes of per-step effects.
 *
 * Primary bytes, 24 bits little-endian: pitch bits 0-4 (0 = no lock, 1..25 = one semitone
 * per code around 13), bit 5 inert, volume 6-11, filter 12-17, resonance 18-23 (0 = no
 * lock in each). Auxiliary byte: the note's timing in the high nibble and key-1 in the low,
 * 0 no note. The timing is a melodic note's length in steps (F, the default, plays the
 * sample to its end as far as measured) and a drum note's retrigger count (1, the default,
 * a single hit; the device's cycle is 1, 2, 3, 4, 6, 8): docs/aux-nibble-results.md. A cell with primary bytes but no note is a parameter lock. Footer byte k:
 * step 2k+1 in the high nibble, step 2k+2 in the low nibble, FX key - 1, F = none.
 */

export const STEPS = 16;
export const SOUNDS = 16;
export const MELODIC_SOUNDS = [1, 2, 3, 4, 5, 6, 7, 8];
export const DRUM_SOUNDS = [9, 10, 11, 12, 13, 14, 15, 16];
export const NO_EFFECT = 0xf;
export const PITCH_CENTER = 13;

export interface Parameters {
  /** 0 = no lock, 1..25 */
  pitch: number;
  /** 0 = no lock, 1..63 */
  volume: number;
  filter: number;
  resonance: number;
  /** Inert bit 5, preserved. */
  bit5?: number;
}

export interface Cell extends Parameters {
  /** Key 1..16, or null for a parameter lock without a note. */
  key: number | null;
  /**
   * The note's timing nibble, 1..15, only when it differs from the sound's default (15 for a
   * melodic sound, 1 for a drum): a melodic note's length in steps, a drum note's retrigger
   * count. It belongs to the note alone; it is not a lock that carries to later steps.
   */
  timing?: number;
}

/** The timing a note has when none is given: a melodic note plays its full length (F), a drum note one hit. */
export function defaultTiming(sound: number): number {
  return sound <= 8 ? 0xf : 1;
}

/** A drum note's retrigger counts, as the device cycles through them. */
export const DRUM_REPEATS = [1, 2, 3, 4, 6, 8] as const;

/**
 * The hits a drum note plays in its step. Nibbles 5 and 7 play as 6 and 8 (measured); the
 * others above 8 were not measured and are read as written.
 */
export function drumRepeats(cell: Cell): number {
  const n = cell.timing ?? 1;
  return n === 5 ? 6 : n === 7 ? 8 : n;
}

/** A melodic note's length in steps, or null for the full sample (F, the default). */
export function melodicLength(cell: Cell): number | null {
  const n = cell.timing ?? 0xf;
  return n === 0xf ? null : n;
}

/** The same note with the sound's default timing: a new note copies a neighbour's parameters, not its timing. */
export function withDefaultTiming(cell: Cell): Cell {
  if (cell.timing === undefined) return cell;
  const copy = { ...cell };
  delete copy.timing;
  return copy;
}

export const NO_LOCKS: Parameters = { pitch: 0, volume: 0, filter: 0, resonance: 0 };
/** The parameters every generated note carried in the verified project builds. */
export const DEFAULT_PARAMETERS: Parameters = { pitch: 13, volume: 36, filter: 63, resonance: 1 };

export function emptyPattern(): Uint8Array {
  const data = new Uint8Array(1032);
  data.fill(0xff, 1024);
  return data;
}

export function cellOffsets(step: number, sound: number): { primary: number; aux: number } {
  checkRange(step, 1, STEPS, 'step');
  checkRange(sound, 1, SOUNDS, 'sound');
  return { primary: 48 * (step - 1) + 3 * (sound - 1), aux: 768 + 16 * (step - 1) + (sound - 1) };
}

export function encodeParameters(p: Parameters): number {
  checkRange(p.pitch, 0, 25, 'pitch');
  checkRange(p.volume, 0, 63, 'volume');
  checkRange(p.filter, 0, 63, 'filter');
  checkRange(p.resonance, 0, 63, 'resonance');
  // One bit: anything else would spill into the volume (2) or every field above it (-1).
  checkRange(p.bit5 ?? 0, 0, 1, 'bit5');
  return p.pitch | ((p.bit5 ?? 0) << 5) | (p.volume << 6) | (p.filter << 12) | (p.resonance << 18);
}

export function decodeParameters(value: number): Required<Parameters> {
  return {
    pitch: value & 31,
    bit5: (value >> 5) & 1,
    volume: (value >> 6) & 63,
    filter: (value >> 12) & 63,
    resonance: (value >> 18) & 63,
  };
}

export function auxByte(sound: number, key: number, timing = defaultTiming(sound)): number {
  checkRange(key, 1, 16, 'key');
  // Nibble 0 with key 1 would be the byte 0, which means no note.
  checkRange(timing, 1, 15, 'timing');
  return (timing << 4) | (key - 1);
}

/** Key 1..16 of an auxiliary byte, or null for no note. Other high nibbles play as notes too. */
export function keyFromAux(aux: number): number | null {
  return aux === 0 ? null : (aux & 0xf) + 1;
}

export function readCell(pattern: Uint8Array, step: number, sound: number): Cell | null {
  const { primary, aux } = cellOffsets(step, sound);
  const value = pattern[primary] | (pattern[primary + 1] << 8) | (pattern[primary + 2] << 16);
  if (pattern[aux] === 0 && value === 0) return null;
  const key = keyFromAux(pattern[aux]);
  const cell: Cell = { key, ...decodeParameters(value) };
  const timing = pattern[aux] >> 4;
  if (key !== null && timing !== defaultTiming(sound)) cell.timing = timing;
  return cell;
}

export function writeCell(pattern: Uint8Array, step: number, sound: number, cell: Cell | null): void {
  const { primary, aux } = cellOffsets(step, sound);
  if (!cell) {
    pattern[primary] = pattern[primary + 1] = pattern[primary + 2] = 0;
    pattern[aux] = 0;
    return;
  }
  const value = encodeParameters(cell);
  pattern[primary] = value & 0xff;
  pattern[primary + 1] = (value >> 8) & 0xff;
  pattern[primary + 2] = (value >> 16) & 0xff;
  pattern[aux] = cell.key === null ? 0 : auxByte(sound, cell.key, cell.timing);
}

export function readEffects(pattern: Uint8Array): (number | null)[] {
  const out: (number | null)[] = [];
  for (let k = 0; k < 8; k++) {
    for (const code of [pattern[1024 + k] >> 4, pattern[1024 + k] & 0xf]) out.push(code === NO_EFFECT ? null : code + 1);
  }
  return out;
}

export function writeEffects(pattern: Uint8Array, effects: (number | null)[]): void {
  if (effects.length !== STEPS) throw new Error('Sixteen step effects are required');
  const codes = effects.map((fx) => {
    if (fx === null) return NO_EFFECT;
    checkRange(fx, 1, 15, 'effect');
    return fx - 1;
  });
  for (let k = 0; k < 8; k++) pattern[1024 + k] = (codes[2 * k] << 4) | codes[2 * k + 1];
}

export function patternIsEmpty(pattern: Uint8Array): boolean {
  for (let i = 0; i < 1024; i++) if (pattern[i]) return false;
  for (let i = 1024; i < 1032; i++) if (pattern[i] !== 0xff) return false;
  return true;
}

function checkRange(value: number, low: number, high: number, name: string): void {
  if (!Number.isInteger(value) || value < low || value > high) {
    throw new Error(`${name} must be an integer ${low}..${high}, got ${value}`);
  }
}

export const PARAMETER_NAMES = ['pitch', 'volume', 'filter', 'resonance'] as const;
export type ParameterName = (typeof PARAMETER_NAMES)[number];

/**
 * The steps of one sound whose locks change a parameter, with the parameters they change:
 * a nonzero code that differs from the value held before the step, which is the last lock
 * before it, round the pattern. The device records the knob positions with every note, so
 * a note that repeats the held values changes nothing, a zero code (no lock) changes
 * nothing, and a lock with no earlier lock to compare with is the baseline.
 */
export function changedParameters(data: Uint8Array, sound: number): Map<number, ParameterName[]> {
  const out = new Map<number, ParameterName[]>();
  for (let step = 1; step <= 16; step++) {
    const cell = readCell(data, step, sound);
    if (!cell) continue;
    const changed = PARAMETER_NAMES.filter((name) => {
      const own = cell[name];
      if (!own) return false;
      const held = heldBefore(data, step, sound, name);
      return held !== null && held !== own;
    });
    if (changed.length) out.set(step, changed);
  }
  return out;
}

/** The last lock of a parameter before a step, round the pattern, or null when no other step locks it. */
function heldBefore(data: Uint8Array, step: number, sound: number, parameter: ParameterName): number | null {
  for (let back = 1; back < 16; back++) {
    const at = ((step - 1 - back + 16) % 16) + 1;
    const code = readCell(data, at, sound)?.[parameter] ?? 0;
    if (code) return code;
  }
  return null;
}

/** The keys one sound plays in a pattern (notes only, not locks without a note). */
export function keysUsed(data: Uint8Array, sound: number): Set<number> {
  const keys = new Set<number>();
  for (let step = 1; step <= 16; step++) {
    const key = readCell(data, step, sound)?.key;
    if (key) keys.add(key);
  }
  return keys;
}

/**
 * The code a step effectively uses for a parameter: its own lock, else the last lock before
 * it in the pattern, wrapping round from step 16 (the device keeps the last locked value),
 * else null when nothing in the pattern locks it.
 */
export function effectiveParameter(data: Uint8Array, step: number, sound: number, parameter: ParameterName): { code: number; own: boolean } | null {
  const own = readCell(data, step, sound)?.[parameter] ?? 0;
  if (own) return { code: own, own: true };
  const held = heldBefore(data, step, sound, parameter);
  return held === null ? null : { code: held, own: false };
}

