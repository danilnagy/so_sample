/** The device's signed mu-law sample codes at 23437.5 Hz. */

export const SAMPLE_RATE = 23437.5;

export function decodeMulaw(code: number): number {
  const coded = code & 128 ? code & 127 : code ^ 255;
  const inverted = coded ^ 255;
  const magnitude = ((((inverted & 15) << 3) + 132) << ((inverted >> 4) & 7)) - 132;
  return magnitude === 0 ? 0 : (inverted & 128 ? -magnitude : magnitude) / 32768;
}

export const MULAW_LEVELS: Float64Array = Float64Array.from({ length: 256 }, (_, code) => decodeMulaw(code));

/** Codes 0..254 sorted by level; 255 duplicates code 0 (negative zero) and is never emitted. */
const SORTED = Array.from({ length: 255 }, (_, code) => code).sort((a, b) => MULAW_LEVELS[a] - MULAW_LEVELS[b]);
const SORTED_LEVELS = Float64Array.from(SORTED, (code) => MULAW_LEVELS[code]);

/** Nearest code for a sample in [-1, 1]; ties go to the lower level. */
export function encodeMulawSample(sample: number): number {
  let lo = 0;
  let hi = SORTED_LEVELS.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (SORTED_LEVELS[mid] < sample) lo = mid + 1;
    else hi = mid;
  }
  const upper = Math.min(lo, SORTED_LEVELS.length - 1);
  const lower = Math.max(upper - 1, 0);
  const pick = Math.abs(sample - SORTED_LEVELS[lower]) <= Math.abs(sample - SORTED_LEVELS[upper]) ? lower : upper;
  return SORTED[pick];
}

export function encodeMulaw(samples: ArrayLike<number>): Uint8Array {
  const out = new Uint8Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    const s = samples[i];
    if (!Number.isFinite(s) || Math.abs(s) > 1) throw new Error('Samples must be finite and within [-1, 1]');
    out[i] = encodeMulawSample(s);
  }
  return out;
}

export function decodeMulawCodes(codes: Uint8Array): Float64Array {
  const out = new Float64Array(codes.length);
  for (let i = 0; i < codes.length; i++) out[i] = MULAW_LEVELS[codes[i]];
  return out;
}
