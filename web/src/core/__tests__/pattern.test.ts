import { describe, expect, it } from 'vitest';

import { DEFAULT_PARAMETERS, auxByte, cellOffsets, changedParameters, decodeParameters, drumRepeats, effectiveParameter, emptyPattern, encodeParameters, keysUsed, melodicLength, readCell, withDefaultTiming, writeCell } from '../pattern';

const note = (key: number, changes: Partial<typeof DEFAULT_PARAMETERS> = {}) => ({ key, ...DEFAULT_PARAMETERS, ...changes });

describe('changed parameters', () => {
  it('marks the steps whose locks change the value held before them, round the pattern', () => {
    const data = emptyPattern();
    writeCell(data, 1, 9, note(1));
    writeCell(data, 5, 9, note(2));
    writeCell(data, 9, 9, note(1, { pitch: 25 }));
    writeCell(data, 13, 9, note(3));
    writeCell(data, 1, 10, note(1, { volume: 49 }));
    // Step 9 raises the pitch and step 13 brings it back; the other steps repeat what is held.
    const changes = changedParameters(data, 9);
    expect([...changes.keys()]).toEqual([9, 13]);
    expect(changes.get(9)).toEqual(['pitch']);
    expect(changes.get(13)).toEqual(['pitch']);
    // The key is not a parameter, and another sound's notes do not count.
    expect(changes.has(5)).toBe(false);
    expect(changedParameters(data, 10).size).toBe(0);
  });

  it('counts a lock without a note, and the note after it that returns the value', () => {
    const data = emptyPattern();
    writeCell(data, 1, 9, note(1));
    writeCell(data, 3, 9, { key: null, pitch: 0, volume: 44, filter: 0, resonance: 0 });
    writeCell(data, 5, 9, note(1));
    const changes = changedParameters(data, 9);
    expect([...changes.keys()]).toEqual([3, 5]);
    expect(changes.get(3)).toEqual(['volume']);
    expect(changes.get(5)).toEqual(['volume']);
  });

  it('marks nothing when every lock repeats the held value, when a code is 0, or when there is nothing before to compare with', () => {
    const data = emptyPattern();
    expect(changedParameters(data, 1).size).toBe(0);
    writeCell(data, 1, 1, note(1, { volume: 49, resonance: 32 }));
    expect(changedParameters(data, 1).size).toBe(0);
    writeCell(data, 2, 1, note(5, { volume: 49, resonance: 32 }));
    writeCell(data, 3, 1, note(5, { volume: 0, resonance: 0 }));
    expect(changedParameters(data, 1).size).toBe(0);
  });

  it('marks both steps of two alternating values', () => {
    const data = emptyPattern();
    writeCell(data, 1, 2, note(1, { pitch: 10 }));
    writeCell(data, 2, 2, note(1, { pitch: 20 }));
    expect([...changedParameters(data, 2).keys()]).toEqual([1, 2]);
  });
});

describe('keys used', () => {
  it('lists the keys a sound plays, ignoring locks without a note and other sounds', () => {
    const data = emptyPattern();
    writeCell(data, 1, 9, note(1));
    writeCell(data, 5, 9, note(5));
    writeCell(data, 9, 9, note(1));
    writeCell(data, 3, 9, { key: null, pitch: 0, volume: 44, filter: 0, resonance: 0 });
    writeCell(data, 2, 10, note(16));
    expect([...keysUsed(data, 9)].sort((a, b) => a - b)).toEqual([1, 5]);
    expect([...keysUsed(data, 10)]).toEqual([16]);
    expect(keysUsed(data, 11).size).toBe(0);
  });
});

describe('effective parameter', () => {
  it('uses the step\'s own lock, else the last lock before it, wrapping round the pattern', () => {
    const data = emptyPattern();
    writeCell(data, 4, 1, note(1, { volume: 40 }));
    writeCell(data, 9, 1, { key: null, pitch: 0, volume: 20, filter: 0, resonance: 0 });
    writeCell(data, 12, 1, note(2, { volume: 0 }));
    expect(effectiveParameter(data, 4, 1, 'volume')).toEqual({ code: 40, own: true });
    expect(effectiveParameter(data, 6, 1, 'volume')).toEqual({ code: 40, own: false });
    expect(effectiveParameter(data, 9, 1, 'volume')).toEqual({ code: 20, own: true });
    expect(effectiveParameter(data, 12, 1, 'volume')).toEqual({ code: 20, own: false });
    expect(effectiveParameter(data, 2, 1, 'volume')).toEqual({ code: 20, own: false });
    expect(effectiveParameter(data, 2, 1, 'filter')).toEqual({ code: 63, own: false });
    expect(effectiveParameter(data, 2, 2, 'volume')).toBeNull();
  });
});

describe('encodeParameters', () => {
  it('keeps bit 5 to one bit: a larger value would change the volume, a negative one every field', () => {
    expect(decodeParameters(encodeParameters({ ...DEFAULT_PARAMETERS, bit5: 1 })).bit5).toBe(1);
    expect(() => encodeParameters({ ...DEFAULT_PARAMETERS, bit5: 2 })).toThrow(/bit5/);
    expect(() => encodeParameters({ ...DEFAULT_PARAMETERS, bit5: -1 })).toThrow(/bit5/);
  });
});

describe('note timing (the auxiliary high nibble: docs/aux-nibble-results.md)', () => {
  it('a default note carries no timing and writes F (melodic) or 1 (drum), as before', () => {
    const data = emptyPattern();
    writeCell(data, 1, 1, { key: 5, ...DEFAULT_PARAMETERS });
    writeCell(data, 1, 9, { key: 3, ...DEFAULT_PARAMETERS });
    expect(data[cellOffsets(1, 1).aux]).toBe(0xf4);
    expect(data[cellOffsets(1, 9).aux]).toBe(0x12);
    expect(readCell(data, 1, 1)).toEqual({ key: 5, ...DEFAULT_PARAMETERS, bit5: 0 });
    expect(readCell(data, 1, 1)!.timing).toBeUndefined();
    expect(readCell(data, 1, 9)!.timing).toBeUndefined();
  });

  it('writes and reads a melodic length and a drum retrigger in the high nibble, beside the key', () => {
    const data = emptyPattern();
    writeCell(data, 2, 1, { key: 5, ...DEFAULT_PARAMETERS, timing: 4 });
    writeCell(data, 2, 9, { key: 3, ...DEFAULT_PARAMETERS, timing: 6 });
    expect(data[cellOffsets(2, 1).aux]).toBe(0x44);
    expect(data[cellOffsets(2, 9).aux]).toBe(0x62);
    expect(readCell(data, 2, 1)).toMatchObject({ key: 5, timing: 4 });
    expect(readCell(data, 2, 9)).toMatchObject({ key: 3, timing: 6 });
    // A melodic 1 and a drum F are not defaults: they are kept.
    data[cellOffsets(3, 1).aux] = 0x14;
    data[cellOffsets(3, 9).aux] = 0xf2;
    expect(readCell(data, 3, 1)).toMatchObject({ key: 5, timing: 1 });
    expect(readCell(data, 3, 9)).toMatchObject({ key: 3, timing: 15 });
  });

  it('refuses a timing of 0 (with key 1 it would be the byte that means no note) or above 15', () => {
    expect(() => auxByte(9, 1, 0)).toThrow(/timing/);
    expect(() => auxByte(1, 1, 16)).toThrow(/timing/);
  });

  it('reads what the device plays: drum nibbles 5 and 7 as 6 and 8 hits, melodic F as the full sample', () => {
    const drum = (timing?: number) => drumRepeats({ key: 1, ...DEFAULT_PARAMETERS, timing });
    expect([undefined, 2, 3, 4, 5, 6, 7, 8].map(drum)).toEqual([1, 2, 3, 4, 6, 6, 8, 8]);
    const melodic = (timing?: number) => melodicLength({ key: 5, ...DEFAULT_PARAMETERS, timing });
    expect([undefined, 15, 1, 4, 14].map(melodic)).toEqual([null, null, 1, 4, 14]);
  });

  it('withDefaultTiming drops only the timing', () => {
    const cell = { key: 2, ...DEFAULT_PARAMETERS, volume: 50, timing: 3 };
    expect(withDefaultTiming(cell)).toEqual({ key: 2, ...DEFAULT_PARAMETERS, volume: 50 });
    expect(cell.timing).toBe(3);
  });
});
