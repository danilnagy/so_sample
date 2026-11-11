/**
 * Shared pieces of the aux-nibble follow-up builds (build-aux-nibble-2-test.ts and
 * build-aux-nibble-3-test.ts): test sounds, raw auxiliary-nibble notes, the layout check and
 * the files the prepare scripts register. The auxiliary byte is written raw, after the cell,
 * as in build-aux-nibble-test.ts, so these builds do not depend on how the app models it.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { bytesToBase64 } from '../src/core/bytes';
import { labelsForBody } from '../src/core/labels';
import { encodeRestoreWav } from '../src/core/modem/encode';
import { SAMPLE_RATE, encodeMulaw } from '../src/core/mulaw';
import { encodePackets } from '../src/core/packets';
import { DEFAULT_PARAMETERS, cellOffsets, readCell, readEffects, writeCell } from '../src/core/pattern';
import { type Clip, type Project, compileProject } from '../src/core/project';
import { serializeState, usedPages } from '../src/core/state';
import { emptyTemplateState } from '../src/core/template';

const RATE = SAMPLE_RATE;

/** Deterministic noise in -1..1. */
function noise(n: number, seed: number): Float64Array {
  const out = new Float64Array(n);
  let x = seed >>> 0 || 1;
  for (let i = 0; i < n; i++) {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0;
    out[i] = (x / 2 ** 32) * 2 - 1;
  }
  return out;
}

/** A two-pole band-pass (RBJ, constant peak gain), in place. */
function bandPass(x: Float64Array, hz: number, q: number): Float64Array {
  const w = (2 * Math.PI * hz) / RATE;
  const alpha = Math.sin(w) / (2 * q);
  const a0 = 1 + alpha;
  const [b0, b2, a1, a2] = [alpha / a0, -alpha / a0, (-2 * Math.cos(w)) / a0, (1 - alpha) / a0];
  let [x1, x2, y1, y2] = [0, 0, 0, 0];
  for (let i = 0; i < x.length; i++) {
    const y = b0 * x[i] + b2 * x2 - a1 * y1 - a2 * y2;
    [x2, x1, y2, y1] = [x1, x[i], y1, y];
    x[i] = y;
  }
  return x;
}

function peak(x: Float64Array): number {
  let m = 0;
  for (const v of x) m = Math.max(m, Math.abs(v));
  return m;
}

/** A steady sine with 10 ms fades. */
export function tone(hz: number, seconds: number, level = 0.7): Uint8Array {
  const n = Math.round(seconds * RATE);
  const fade = Math.round(0.01 * RATE);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) out[i] = level * Math.sin((2 * Math.PI * hz * i) / RATE) * Math.min(1, i / fade, (n - i) / fade);
  return encodeMulaw(out);
}

/** A short sine burst decaying with time constant `tau`: a sharp, separate onset. */
export function click(hz: number, seconds: number, tau: number, level = 0.9): Uint8Array {
  const n = Math.round(seconds * RATE);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) out[i] = level * Math.sin((2 * Math.PI * hz * i) / RATE) * Math.exp(-i / (tau * RATE));
  return encodeMulaw(out);
}

/**
 * A struck drum: a sharp click at `clickHz` (its onset), then a body of band-passed noise
 * around `bodyHz` decaying with amplitude time constant `bodyTau`, `seconds` long. Noise, so
 * two overlapping copies add in power rather than interfering.
 */
export function strike(clickHz: number, bodyHz: number, bodyTau: number, seconds: number): Uint8Array {
  const n = Math.round(seconds * RATE);
  const body = bandPass(noise(n, 77), bodyHz, 1.2);
  const scale = 0.45 / (peak(body.subarray(0, Math.round(0.05 * RATE))) || 1);
  const fade = Math.round(0.01 * RATE);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const clickPart = 0.45 * Math.sin(2 * Math.PI * clickHz * t) * Math.exp(-t / 0.0012);
    out[i] = clickPart + body[i] * scale * Math.exp(-t / bodyTau) * Math.min(1, (n - i) / fade);
  }
  return encodeMulaw(out);
}

export interface Probe {
  pattern: number;
  step: number;
  sound: number;
  key: number;
  nibble: number;
}

export interface Written extends Probe {
  offset: number;
  byte: number;
}

/** A note with DEFAULT parameters, then its auxiliary byte rewritten with the probe's high nibble. */
export function writeProbe(project: Project, p: Probe): Written {
  const data = project.patterns[p.pattern - 1];
  writeCell(data, p.step, p.sound, { key: p.key, ...DEFAULT_PARAMETERS });
  const { aux } = cellOffsets(p.step, p.sound);
  const byte = (p.nibble << 4) | (p.key - 1);
  data[aux] = byte;
  return { ...p, offset: aux, byte };
}

/**
 * Compile, check the layout (every written byte arrives, the notes are exactly the probes,
 * the effects are as given), and write restore.wav, packets.json and project.json.
 */
export function compileAndWrite(
  out: string,
  project: Project,
  library: Map<string, Uint8Array>,
  written: Written[],
  effects: { pattern: number; effects: (number | null)[] }[],
  facts: Record<string, unknown>,
): Record<string, number> {
  const state = compileProject(project, (id) => library.get(id)!, emptyTemplateState());
  const expect = (what: string, ok: boolean) => {
    if (!ok) throw new Error(`Unexpected layout: ${what}`);
  };
  for (const w of written) {
    const data = state.patterns[w.pattern - 1];
    expect(`pattern ${w.pattern} step ${w.step} sound ${w.sound} aux byte`, data[w.offset] === w.byte);
    expect(`pattern ${w.pattern} step ${w.step} sound ${w.sound} key`, readCell(data, w.step, w.sound)?.key === w.key);
  }
  let notes = 0;
  state.patterns.forEach((data) => {
    for (let step = 1; step <= 16; step++) for (let sound = 1; sound <= 16; sound++) if (readCell(data, step, sound)?.key) notes++;
  });
  expect('one note per probe and no others', notes === written.length);
  for (const e of effects) {
    const read = readEffects(state.patterns[e.pattern - 1]);
    expect(`pattern ${e.pattern} effects`, read.every((fx, i) => fx === e.effects[i]));
  }
  const packets = serializeState(state);
  const body = encodePackets(packets);
  const wav = encodeRestoreWav(labelsForBody(body));
  mkdirSync(out, { recursive: true });
  writeFileSync(resolve(out, 'restore.wav'), wav);
  writeFileSync(resolve(out, 'packets.json'), JSON.stringify({ schema: 'sosample.packets', packets: packets.map((p) => ({ tag: p.tag, payload: bytesToBase64(p.payload) })) }));
  writeFileSync(
    resolve(out, 'project.json'),
    JSON.stringify(
      {
        ...facts,
        tempo: project.tempo,
        swing: project.swing,
        chain: project.chain,
        aux_bytes: written.map((w) => ({ pattern: w.pattern, step: w.step, sound: w.sound, offset: w.offset, byte: w.byte })),
        effects,
        patterns: project.patterns.map(bytesToBase64),
        samples: Object.fromEntries([...library].map(([id, codes]) => [id, { codes: codes.length, base64: bytesToBase64(codes) }])),
      },
      null,
      1,
    ),
  );
  return { pages: usedPages(state), packets: packets.length, bodyBytes: body.length, wavBytes: wav.length, seconds: (wav.length - 44) / 4 / 44100 };
}

/** The whole sample as a clip. */
export const whole = (library: Map<string, Uint8Array>, id: string): Clip => ({ sampleId: id, start: 0, end: library.get(id)!.length });
