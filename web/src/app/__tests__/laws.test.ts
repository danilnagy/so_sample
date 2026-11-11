import { describe, expect, it } from 'vitest';

import { BASE_KEY, keyMeaning, keySemitones, rollKeys } from '../laws';

describe('keys from the base key', () => {
  it('places key 5 at the original pitch and the scale above and an octave below it', () => {
    expect(BASE_KEY).toBe(5);
    // Observed on the device: 5, 6, 7, 8, 1, 2, 3, 4 rise; 13..16, 9..12 repeat an octave lower.
    expect([5, 6, 7, 8, 1, 2, 3, 4].map(keySemitones)).toEqual([0, 2, 3, 5, 7, 8, 10, 11]);
    expect([13, 14, 15, 16, 9, 10, 11, 12].map(keySemitones)).toEqual([-12, -10, -9, -7, -5, -4, -2, -1]);
    expect(keyMeaning(5, true)).toBe('0 st, base key');
    expect(keyMeaning(1, true)).toBe('+7 st');
    expect(keyMeaning(13, true)).toBe('-12 st');
    expect(keyMeaning(3, false)).toBe('slice 3');
  });

  it('orders roll rows by pitch for a melodic sound, in groups that are the device key rows, and by key for a kit', () => {
    expect(rollKeys(true)).toEqual([4, 3, 2, 1, 8, 7, 6, 5, 12, 11, 10, 9, 16, 15, 14, 13]);
    expect(rollKeys(false)).toEqual(Array.from({ length: 16 }, (_, k) => k + 1));
  });
});
