/**
 * Synthesized drum hits for the standard kits: a freely licensed mirror of the TR-series
 * kits, built from oscillators and seeded noise, so the bundled kits and projects carry no
 * third-party audio.
 *
 * Each hit is chosen from the name of the sample it stands in for ("TR-808 Low Conga 01" is
 * a low conga, "02" a slightly different one) and shaped by its machine's character: the
 * 808's long sine kick and tonal snare, the 909's clicky kick and noisy snare, the thinner
 * 606, the shorter, brighter 505, 626 and 707. The classic 808 recipes (decaying sines with
 * a falling pitch, six detuned square waves for the metal, band-passed noise for the hats,
 * snares and claps) apply to every machine; only their settings differ.
 *
 * Everything is deterministic: the same build writes the same codes.
 */

import { SAMPLE_RATE } from '../src/core/mulaw';

const RATE = SAMPLE_RATE;

/** Deterministic white noise in -1..1 (a linear congruential generator). */
function noise(n: number, seed: number): Float64Array {
  const out = new Float64Array(n);
  let x = seed >>> 0 || 1;
  for (let i = 0; i < n; i++) {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0;
    out[i] = (x / 2 ** 32) * 2 - 1;
  }
  return out;
}

/** A two-pole band-pass (RBJ cookbook, constant peak gain), in place. */
function bandPass(x: Float64Array, hz: number, q: number): Float64Array {
  const w = (2 * Math.PI * Math.min(hz, RATE * 0.45)) / RATE;
  const alpha = Math.sin(w) / (2 * q);
  const a0 = 1 + alpha;
  const b0 = alpha / a0;
  const b2 = -alpha / a0;
  const a1 = (-2 * Math.cos(w)) / a0;
  const a2 = (1 - alpha) / a0;
  let x1 = 0;
  let x2 = 0;
  let y1 = 0;
  let y2 = 0;
  for (let i = 0; i < x.length; i++) {
    const y = b0 * x[i] + b2 * x2 - a1 * y1 - a2 * y2;
    x2 = x1;
    x1 = x[i];
    y2 = y1;
    y1 = y;
    x[i] = y;
  }
  return x;
}

/** A one-pole high-pass, in place. */
function highPass(x: Float64Array, hz: number): Float64Array {
  const rc = 1 / (2 * Math.PI * hz);
  const a = rc / (rc + 1 / RATE);
  let prevX = 0;
  let prevY = 0;
  for (let i = 0; i < x.length; i++) {
    const y = a * (prevY + x[i] - prevX);
    prevX = x[i];
    prevY = y;
    x[i] = y;
  }
  return x;
}

const decay = (i: number, seconds: number) => Math.exp(-i / (seconds * RATE));

/** A sine whose pitch falls from `from` to `to` Hz, decaying: kicks, toms, congas, the 808 bass. */
function fallingSine(seconds: number, from: number, to: number, fall: number, ring: number, drive = 1): Float64Array {
  const n = Math.round(seconds * RATE);
  const out = new Float64Array(n);
  let phase = 0;
  for (let i = 0; i < n; i++) {
    const hz = to + (from - to) * decay(i, fall);
    phase += (2 * Math.PI * hz) / RATE;
    const v = Math.sin(phase) * decay(i, ring);
    out[i] = drive === 1 ? v : Math.tanh(v * drive) / Math.tanh(drive);
  }
  return out;
}

/** The 808's metal: six square waves at inharmonic ratios, summed. */
const METAL = [205.3, 304.4, 369.6, 522.7, 540, 800];
function metal(n: number, scale: number): Float64Array {
  const out = new Float64Array(n);
  for (const f of METAL) {
    const hz = f * scale;
    for (let i = 0; i < n; i++) out[i] += Math.sign(Math.sin((2 * Math.PI * hz * i) / RATE)) / METAL.length;
  }
  return out;
}

function mix(...parts: [Float64Array, number][]): Float64Array {
  const n = Math.max(...parts.map(([p]) => p.length));
  const out = new Float64Array(n);
  for (const [p, gain] of parts) for (let i = 0; i < p.length; i++) out[i] += p[i] * gain;
  return out;
}

function shaped(x: Float64Array, ring: number, attack = 0): Float64Array {
  const a = Math.round(attack * RATE);
  for (let i = 0; i < x.length; i++) x[i] *= decay(i, ring) * (a && i < a ? i / a : 1);
  return x;
}

/** Scale to a peak of `peak`. */
function normalized(x: Float64Array, peak = 0.9): Float64Array {
  let max = 0;
  for (const v of x) max = Math.max(max, Math.abs(v));
  if (max > 0) for (let i = 0; i < x.length; i++) x[i] *= peak / max;
  return x;
}

/** A machine's character: the settings its hits share. */
interface Character {
  kick: { from: number; to: number; fall: number; ring: number; drive: number; click: number };
  snare: { tone: number; ring: number; noise: number; bright: number };
  /** Metal pitch scale and how much noise the hats carry beside it. */
  hat: { scale: number; noise: number; bright: number };
  tom: { low: number; ring: number };
  /** Hits are shortened by this factor: the digital machines are tighter. */
  tight: number;
}

const CHARACTERS: Record<string, Character> = {
  '505': { kick: { from: 150, to: 56, fall: 0.03, ring: 0.16, drive: 1.6, click: 0.15 }, snare: { tone: 210, ring: 0.09, noise: 0.6, bright: 4000 }, hat: { scale: 1.25, noise: 0.5, bright: 7500 }, tom: { low: 110, ring: 0.16 }, tight: 0.8 },
  '606': { kick: { from: 140, to: 62, fall: 0.025, ring: 0.13, drive: 1.2, click: 0.1 }, snare: { tone: 230, ring: 0.07, noise: 0.75, bright: 4500 }, hat: { scale: 1.1, noise: 0.3, bright: 7000 }, tom: { low: 120, ring: 0.14 }, tight: 0.85 },
  '626': { kick: { from: 160, to: 54, fall: 0.03, ring: 0.18, drive: 1.5, click: 0.15 }, snare: { tone: 200, ring: 0.1, noise: 0.6, bright: 4200 }, hat: { scale: 1.2, noise: 0.5, bright: 7200 }, tom: { low: 100, ring: 0.18 }, tight: 0.85 },
  '707': { kick: { from: 170, to: 55, fall: 0.03, ring: 0.2, drive: 1.4, click: 0.2 }, snare: { tone: 190, ring: 0.1, noise: 0.55, bright: 4000 }, hat: { scale: 1.15, noise: 0.55, bright: 7000 }, tom: { low: 95, ring: 0.2 }, tight: 0.9 },
  '808': { kick: { from: 110, to: 48, fall: 0.04, ring: 0.32, drive: 1, click: 0.04 }, snare: { tone: 180, ring: 0.12, noise: 0.42, bright: 3500 }, hat: { scale: 1, noise: 0.1, bright: 6500 }, tom: { low: 85, ring: 0.26 }, tight: 1 },
  '909': { kick: { from: 230, to: 52, fall: 0.02, ring: 0.24, drive: 1.8, click: 0.35 }, snare: { tone: 190, ring: 0.1, noise: 0.68, bright: 5000 }, hat: { scale: 1.3, noise: 0.65, bright: 8000 }, tom: { low: 90, ring: 0.22 }, tight: 1 },
};

/** The machine's number in a kit's machine folder name: "ROLAND TR-808 (1980)" is "808". */
export function machineOf(folder: string): string {
  const m = /(\d{3})/.exec(folder);
  if (!m || !CHARACTERS[m[1]]) throw new Error(`No synthesized character for "${folder}"`);
  return m[1];
}

/** 0 for the first variant of a hit, 1 for the second, and so on: "Kick 02" is 1. */
function variantOf(name: string): number {
  const m = /(\d+)\s*$/.exec(name);
  return m ? Math.max(0, Number(m[1]) - 1) % 4 : 0;
}

/**
 * A synthesized hit standing in for the named sample, `seconds` long at most, as native-rate
 * samples in -1..1. `name` is the original's file name ("TR-909 Open Hat 02").
 */
export function synthHit(machineFolder: string, name: string, key: number, seconds: number): Float64Array {
  const c = CHARACTERS[machineOf(machineFolder)];
  const v = variantOf(name);
  const n = Math.round(seconds * RATE);
  const seed = [...name].reduce((h, ch) => (Math.imul(h, 31) + ch.charCodeAt(0)) >>> 0, 7);
  const is = (re: RegExp) => re.test(name);
  const T = c.tight;
  let x: Float64Array;
  if (is(/808s|BD Long/i)) {
    // The 808 bass: a long sine with a short fall, saturated a little more for each variant.
    x = fallingSine(seconds, 95, 44 + v * 3, 0.03, 0.6, 1 + v * 0.8);
  } else if (is(/kick|BD /i)) {
    const k = c.kick;
    const body = fallingSine(seconds, k.from * (1 + v * 0.12), k.to * (1 - v * 0.05), k.fall, k.ring * (1 + v * 0.25), k.drive);
    const click = shaped(highPass(noise(n, seed), 1500), 0.004);
    x = mix([body, 1], [click, k.click]);
  } else if (is(/snare|SD /i)) {
    const s = c.snare;
    const tone = mix([fallingSine(seconds, s.tone * 1.3, s.tone * (1 + v * 0.1), 0.01, s.ring * 0.8), 1], [fallingSine(seconds, s.tone * 1.9, s.tone * 1.75, 0.01, s.ring * 0.6), 0.6]);
    const hiss = shaped(highPass(bandPass(noise(n, seed), s.bright, 0.7), 900), s.ring * (1.5 + v * 0.5) * T);
    x = mix([tone, 1 - s.noise], [normalized(hiss), s.noise]);
  } else if (is(/rim/i)) {
    x = mix([fallingSine(seconds, 1700 + v * 200, 1650, 0.002, 0.012), 1], [fallingSine(seconds, 520, 500, 0.002, 0.02), 0.6]);
    x = highPass(x, 300);
  } else if (is(/clap/i)) {
    // Three quick bursts and a tail, band-passed.
    const raw = noise(n, seed);
    const env = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const t = i / RATE;
      const burst = [0, 0.011, 0.022].reduce((e, start) => (t >= start ? Math.max(e, decay(i - start * RATE, 0.006)) : e), 0);
      env[i] = Math.max(burst, t >= 0.03 ? 0.6 * decay(i - 0.03 * RATE, 0.06 * (1 + v * 0.3) * T) : 0);
    }
    x = bandPass(raw.map((s, i) => s * env[i]), 1100 + v * 200, 1.2);
  } else if (is(/open hat/i)) {
    const h = c.hat;
    x = mix([highPass(bandPass(metal(n, h.scale * (1 + v * 0.04)), h.bright, 0.8), 5000), 1], [highPass(noise(n, seed), 6000), h.noise]);
    shaped(x, 0.12 * (1 + v * 0.4) * T);
  } else if (is(/hat/i)) {
    const h = c.hat;
    x = mix([highPass(bandPass(metal(n, h.scale * (1 + v * 0.04)), h.bright, 0.8), 5000), 1], [highPass(noise(n, seed), 6000), h.noise]);
    shaped(x, 0.022 * (1 + v * 0.5) * T);
  } else if (is(/ride/i)) {
    const h = c.hat;
    const bell = mix([fallingSine(seconds, 640 * h.scale, 640 * h.scale, 1, 0.5), 0.5], [fallingSine(seconds, 960 * h.scale, 960 * h.scale, 1, 0.35), 0.3]);
    x = mix([shaped(highPass(metal(n, h.scale * 1.5), 3000), 0.35 * T), 1], [bell, 0.35], [shaped(highPass(noise(n, seed), 7000), 0.3), 0.25]);
  } else if (is(/crash|cymbal/i)) {
    const h = c.hat;
    x = mix([highPass(metal(n, h.scale * (0.9 + v * 0.1)), 3500), 0.7], [highPass(noise(n, seed), 4000), 0.7]);
    shaped(x, 0.35 * (1 + v * 0.3) * T, 0.002);
  } else if (is(/cowbell/i)) {
    x = bandPass(squarePair(n, 540 * (1 + v * 0.05), 800 * (1 + v * 0.05)), 2600, 0.6);
    shaped(x, 0.06 * T);
  } else if (is(/conga/i)) {
    const hz = is(/low|lo /i) ? 165 : is(/mid/i) ? 250 : 340;
    x = fallingSine(seconds, hz * 1.4, hz, 0.006, 0.09 * T);
  } else if (is(/clave/i)) {
    x = fallingSine(seconds, 2500, 2500, 1, 0.018);
  } else if (is(/maraca|shaker/i)) {
    x = shaped(highPass(noise(n, seed), 6500), is(/shaker/i) ? 0.035 : 0.018, 0.004);
  } else if (is(/tambourine/i)) {
    x = mix([shaped(highPass(metal(n, 2.2), 6000), 0.06), 0.6], [shaped(highPass(noise(n, seed), 8000), 0.08, 0.002), 0.8]);
  } else if (is(/tom/i)) {
    // Toms by key: 13 low, 14 mid, 15 high (16 a second high on some machines); the name's
    // Lo/Mid/Hi wins where it says.
    const step = is(/lo/i) ? 0 : is(/mid/i) ? 1 : is(/hi/i) ? 2 : Math.max(0, Math.min(3, key - 13));
    const hz = c.tom.low * 1.33 ** step * (1 + v * 0.06);
    x = mix([fallingSine(seconds, hz * 1.6, hz, 0.02, c.tom.ring), 1], [shaped(bandPass(noise(n, seed), hz * 4, 1), 0.02), 0.15]);
  } else {
    // Anything unnamed: a short tonal percussion hit.
    x = fallingSine(seconds, 600, 420, 0.01, 0.05);
  }
  return normalized(x, 0.89);
}

function squarePair(n: number, a: number, b: number): Float64Array {
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) out[i] = (Math.sign(Math.sin((2 * Math.PI * a * i) / RATE)) + Math.sign(Math.sin((2 * Math.PI * b * i) / RATE))) / 2;
  return out;
}

/** The synthesized hit's length: where it has fallen below -54 dB, at most `cap` seconds, and at least 20 ms. */
export function trimmedLength(x: Float64Array, cap: number): number {
  const limit = Math.min(x.length, Math.round(cap * RATE));
  let end = limit;
  while (end > Math.round(0.02 * RATE) && Math.abs(x[end - 1]) < 0.002) end--;
  return end;
}
