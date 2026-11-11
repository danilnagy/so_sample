/** Display meanings of step parameters, from the measured laws (docs/format-reference.md). */

import type { ParameterName } from '../core/pattern';

/** Semitones from key 1 for keys 1..16, as the 4x4 keyboard is laid out (measured, pattern1-key-scale-map). */
export const KEY_SEMITONES = [0, 1, 3, 4, -7, -5, -4, -2, -12, -11, -9, -8, -19, -17, -16, -14];

/**
 * The key that plays a sample at its original pitch. The registered measurement fixes the
 * intervals between keys; the base is a listening observation on the device (2026-11-07):
 * key 5 plays the sample unshifted, keys 6, 7, 8, 1, 2, 3, 4 rise through the scale
 * (+2, +3, +5, +7, +8, +10, +11), and keys 13, 14, 15, 16, 9, 10, 11, 12 repeat it an
 * octave lower (-12 to -1), consistent with the measured intervals.
 */
export const BASE_KEY = 5;

/** Semitones of a melodic key from the base key. */
export function keySemitones(key: number): number {
  return KEY_SEMITONES[key - 1] - KEY_SEMITONES[BASE_KEY - 1];
}

/** The keys as rows of a roll: a melodic sound by pitch, highest first; a drum kit by key, 1..16. */
export function rollKeys(melodic: boolean): number[] {
  const keys = Array.from({ length: 16 }, (_, k) => k + 1);
  return melodic ? keys.sort((a, b) => keySemitones(b) - keySemitones(a)) : keys;
}

export function semitoneLabel(semitones: number): string {
  return semitones === 0 ? '0 st' : `${semitones > 0 ? '+' : ''}${semitones} st`;
}

/** Measured gain against code 36 (dB), interpolated between the measured codes. */
const VOLUME_POINTS: [number, number][] = [
  [3, -15.4], [6, -14.6], [9, -13.3], [12, -11.8], [18, -8.6], [21, -7.0], [27, -4.0], [30, -2.6],
  [36, 0], [39, 1.2], [45, 3.4], [48, 4.4], [54, 6.2], [60, 7.2], [63, 7.5],
];

export function volumeDb(code: number): number {
  if (code <= VOLUME_POINTS[0][0]) return VOLUME_POINTS[0][1];
  for (let i = 1; i < VOLUME_POINTS.length; i++) {
    const [c1, d1] = VOLUME_POINTS[i];
    if (code <= c1) {
      const [c0, d0] = VOLUME_POINTS[i - 1];
      return d0 + ((d1 - d0) * (code - c0)) / (c1 - c0);
    }
  }
  return VOLUME_POINTS[VOLUME_POINTS.length - 1][1];
}

function hz(value: number): string {
  return value >= 1000 ? `${(value / 1000).toFixed(1)} kHz` : `${Math.round(value)} Hz`;
}

export function filterMeaning(code: number): string {
  if (code === 0 || code === 63) return 'off';
  if (code <= 26) return `low-pass ${hz(2 ** (0.234 * code + 6.66))}`;
  if (code <= 31) return 'low-pass above 10 kHz';
  if (code <= 43) return 'flat';
  return `high-pass ${hz(2 ** (0.262 * code - 2.94))}`;
}

export function resonanceLevel(code: number): number {
  return Math.floor(code / 8) + 1;
}

export function pitchMeaning(code: number): string {
  return semitoneLabel(code - 13);
}

/** Code range of each step parameter; 0 is "no lock" and lies outside it. */
export const PARAMETER_RANGES: Record<ParameterName, [number, number]> = {
  pitch: [1, 25],
  volume: [1, 63],
  filter: [1, 63],
  resonance: [1, 63],
};

/** One code per resonance level; the codes between sound the same. */
export const RESONANCE_CODES = [1, 8, 16, 24, 32, 40, 48, 56];

export function parameterMeaning(parameter: ParameterName, code: number): string {
  switch (parameter) {
    case 'pitch':
      return pitchMeaning(code);
    case 'volume':
      return `${volumeDb(code) >= 0 ? '+' : ''}${volumeDb(code).toFixed(1)} dB`;
    case 'filter':
      return filterMeaning(code);
    case 'resonance':
      return `level ${resonanceLevel(code)} of 8`;
  }
}

export const PARAMETER_LABELS: Record<ParameterName, string> = { pitch: 'Pitch', volume: 'Vol', filter: 'Filt', resonance: 'Res' };

export function keyMeaning(key: number, melodic: boolean): string {
  if (!melodic) return `slice ${key}`;
  const s = keySemitones(key);
  return s === 0 ? '0 st, base key' : semitoneLabel(s);
}

/** Effect names as the PO-33 guide lists them (teenage.engineering/guides/po-33), by FX key. */
export const FX_NAMES: Record<number, string> = {
  1: 'loop 16',
  2: 'loop 12',
  3: 'loop short',
  4: 'loop shorter',
  5: 'unison',
  6: 'unison low',
  7: 'octave up',
  8: 'octave down',
  9: 'stutter 4',
  10: 'stutter 3',
  11: 'scratch',
  12: 'scratch fast',
  13: '6 / 8 quantize',
  14: 'retrigger pattern',
  15: 'reverse',
};

/** What each effect was measured to do on the device (docs/fx-reference.md), by FX key. */
export const FX_BEHAVIOUR: Record<number, string> = {
  1: 'loops 1/16 of a bar, following the tempo',
  2: 'loops 1/12 of a bar, following the tempo',
  3: 'loops 1/32 of a bar, following the tempo',
  4: 'loops a fixed 80 ms',
  5: 'adds a slightly detuned second onset about 93 ms after each note',
  6: 'adds a copy one octave down',
  7: 'bends the pitch up about an octave over 200 ms',
  8: 'bends the pitch down about an octave over 300 ms',
  9: 'cuts every note short at about half a step',
  10: 'of each four steps, the third starts late and quieter and the fourth is silent',
  11: 'the playback position jumps about the sample',
  12: 'retriggers the first held note once per step',
  13: 'plays the first three notes of each beat as triplets and drops the fourth',
  14: 'loops the steps before the hold, from step 1',
  15: 'plays the sample backwards',
};

/** Voice ranking on a shared step: lowest sound numbers win, Sound 11 after Sound 3. */
export const VOICE_RANK = [1, 2, 3, 11, 4, 5, 6, 7, 8, 12, 13, 14, 15, 16, 9, 10];
