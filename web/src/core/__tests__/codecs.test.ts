import { describe, expect, it } from 'vitest';

import { MULAW_LEVELS, decodeMulawCodes, encodeMulaw } from '../mulaw';
import { resamplePoly } from '../resample';
import { floatToPcm16, parseWav, wavFromPcm16 } from '../wav';
import mulaw from '../__fixtures__/mulaw.json';
import pcm16 from '../__fixtures__/pcm16.json';
import resample from '../__fixtures__/resample.json';

describe('PCM16 conversion', () => {
  it('matches how the accepted restores were written', () => {
    const converted = pcm16.values.map(floatToPcm16);
    expect(converted).toEqual(pcm16.pcm16);
  });

  it('round-trips through a WAV file', () => {
    const pcm = Int16Array.from(pcm16.pcm16.flatMap((v) => [v, -v]));
    const wav = parseWav(wavFromPcm16(pcm, 2, 44100));
    expect(wav.sampleRate).toBe(44100);
    expect(wav.channels.length).toBe(2);
    expect(Array.from(wav.channels[0], (v) => v * 32768)).toEqual(pcm16.pcm16);
  });
});

describe('mu-law', () => {
  it('decodes every code to the reference level', () => {
    expect(Array.from(MULAW_LEVELS)).toEqual(mulaw.levels);
  });

  it('encodes to the nearest code as the reference does', () => {
    expect(Array.from(encodeMulaw(mulaw.encode_input))).toEqual(mulaw.encode_codes);
  });

  it('decodes what it encodes within one quantisation step', () => {
    const codes = encodeMulaw(mulaw.encode_input);
    const decoded = decodeMulawCodes(codes);
    mulaw.encode_input.forEach((x, i) => {
      expect(Math.abs(decoded[i] - x)).toBeLessThan(0.04);
    });
  });
});

describe('resampling', () => {
  it.each(resample.cases.map((c) => [c.input_rate_hz, c] as const))('matches scipy from %d Hz', (_rate, c) => {
    const y = resamplePoly(c.input, c.up, c.down);
    expect(y.length).toBe(c.output.length);
    let maxError = 0;
    for (let i = 0; i < y.length; i++) maxError = Math.max(maxError, Math.abs(y[i] - c.output[i]));
    expect(maxError).toBeLessThan(1e-9);
    const codes = encodeMulaw(Array.from(y, (v) => Math.max(-1, Math.min(1, v))));
    let differing = 0;
    for (let i = 0; i < codes.length; i++) if (codes[i] !== c.output_codes[i]) differing++;
    expect(differing).toBeLessThanOrEqual(2);
  });
});
