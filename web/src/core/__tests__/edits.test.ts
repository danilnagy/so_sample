import { describe, expect, it } from 'vitest';

import { applyModifications, isUnmodified, noModifications, renderModifications } from '../edits';
import { decodeMulawCodes, encodeMulaw } from '../mulaw';

const tone = (length: number, peak: number): Uint8Array =>
  encodeMulaw(Float64Array.from({ length }, (_, i) => peak * Math.sin((2 * Math.PI * 440 * i) / 23437.5)));

describe('modifications', () => {
  it('leaves an unmodified sample untouched', () => {
    const codes = tone(3000, 0.5);
    expect(isUnmodified(noModifications(3000), 3000)).toBe(true);
    expect(applyModifications(codes, undefined)).toBe(codes);
    expect(applyModifications(codes, noModifications(3000))).toBe(codes);
  });

  it('trims and applies gain', () => {
    const codes = tone(3000, 0.25);
    const out = applyModifications(codes, { ...noModifications(3000), start: 1000, end: 2000, gainDb: 6 });
    expect(out.length).toBe(1000);
    const peak = Math.max(...decodeMulawCodes(out).map(Math.abs));
    expect(peak).toBeGreaterThan(0.45);
    expect(peak).toBeLessThan(0.55);
  });

  it('normalises to full scale and clips above it', () => {
    const codes = tone(3000, 0.1);
    const normalized = renderModifications(codes, { ...noModifications(3000), normalize: true });
    expect(Math.max(...normalized.map(Math.abs))).toBeCloseTo(1, 2);
    const hot = renderModifications(codes, { ...noModifications(3000), gainDb: 24 });
    expect(Math.max(...hot.map(Math.abs))).toBe(1);
  });

  it('fades in and out', () => {
    const codes = tone(3000, 0.5);
    const out = renderModifications(codes, { ...noModifications(3000), fadeIn: 500, fadeOut: 500 });
    expect(out[0]).toBe(0);
    expect(out[2999]).toBe(0);
    expect(Math.max(...out.subarray(0, 100).map(Math.abs))).toBeLessThan(0.11);
    expect(Math.max(...out.subarray(1000, 2000).map(Math.abs))).toBeGreaterThan(0.45);
  });

  it('compresses peaks above the threshold', () => {
    const codes = tone(6000, 0.9);
    const out = renderModifications(codes, { ...noModifications(6000), compressor: { thresholdDb: -20, ratio: 4, makeupDb: 0 } });
    const late = Math.max(...out.subarray(3000).map(Math.abs));
    // 0.9 is 19 dB over -20 dBFS; at 4:1 the output sits near -15 dB (0.17), a little
    // above that because the envelope follower reads under the peaks of a sine.
    expect(late).toBeGreaterThan(0.15);
    expect(late).toBeLessThan(0.25);
  });
});
