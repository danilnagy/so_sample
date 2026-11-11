/**
 * Build the restore for the registered hardware test of the TypeScript compile step
 * (docs/web-template-control.md). Writes restore.wav, packets.json and project.json into
 * experiments/web-template-001; scripts/prepare_web_template_test.py registers the test
 * from those files. Run from web/: npx tsx scripts/build-web-template-test.ts
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { bytesToBase64 } from '../src/core/bytes';
import { labelsForBody } from '../src/core/labels';
import { encodeRestoreWav } from '../src/core/modem/encode';
import { encodeMulaw } from '../src/core/mulaw';
import { encodePackets } from '../src/core/packets';
import { DEFAULT_PARAMETERS, writeCell, writeEffects } from '../src/core/pattern';
import { type Project, compileProject, emptyProject } from '../src/core/project';
import { serializeState, usedPages } from '../src/core/state';
import { emptyTemplateState } from '../src/core/template';

const RATE = 23437.5;
const OUT = resolve(import.meta.dirname, '../../experiments/web-template-001');

function tone(seconds: number, hz: number, peak: number): Uint8Array {
  const n = Math.round(seconds * RATE);
  const samples = new Float64Array(n);
  for (let i = 0; i < n; i++) samples[i] = peak * Math.sin((2 * Math.PI * hz * i) / RATE) * Math.exp(-i / (0.7 * n));
  return encodeMulaw(samples);
}

/** Deterministic noise burst (linear congruential), decaying. */
function burst(seconds: number, peak: number, seed: number): Uint8Array {
  const n = Math.round(seconds * RATE);
  const samples = new Float64Array(n);
  let x = seed >>> 0;
  for (let i = 0; i < n; i++) {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0;
    samples[i] = peak * ((x / 2 ** 32) * 2 - 1) * Math.exp(-i / (0.3 * n));
  }
  return encodeMulaw(samples);
}

function chirp(seconds: number, peak: number): Uint8Array {
  const n = Math.round(seconds * RATE);
  const samples = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    samples[i] = peak * Math.sin(2 * Math.PI * (200 * t + ((2000 - 200) * t * t) / (2 * seconds)));
  }
  return encodeMulaw(samples);
}

const library = new Map<string, Uint8Array>([
  ['tone-a', tone(0.5, 329.6, 0.5)], // 11719 codes, 3 pages
  ['kick', burst(0.08, 0.6, 1)], // 1875 codes
  ['snare', burst(0.05, 0.6, 2)], // 1172 codes
  ['chirp', chirp(0.35, 0.5)], // 8203 codes
]);

const project: Project = emptyProject(100);
project.swing = 4;
project.chain = [1, 2];
// Melodic: Sound 1 owns tone-a; Sound 2 references it with a shorter window; Sound 3
// references it from a nonzero start.
project.melodic[0] = { sampleId: 'tone-a', start: 0, end: 11719 };
project.melodic[1] = { sampleId: 'tone-a', start: 0, end: 5000 };
project.melodic[2] = { sampleId: 'tone-a', start: 3000, end: 9000 };
// Drum Sound 9: a kit buffer (kick, snare, kick again as a window) plus an empty key, a
// reference into Sound 1's buffer, and a sample used by several keys.
const kit = { slices: new Array<null | { sampleId: string; start: number; end: number }>(16).fill(null) };
kit.slices[0] = { sampleId: 'kick', start: 0, end: 1875 };
kit.slices[1] = { sampleId: 'snare', start: 0, end: 1172 };
kit.slices[2] = { sampleId: 'kick', start: 400, end: 1875 };
kit.slices[3] = null; // no record: expected silent
kit.slices[4] = { sampleId: 'tone-a', start: 0, end: 4000 };
for (let k = 5; k < 16; k++) kit.slices[k] = { sampleId: 'snare', start: 0, end: 1172 };
project.drums[0] = kit;
// Drum Sound 10: one sample sliced into sixteen windows, one of them overlapping.
const sliced = { slices: Array.from({ length: 16 }, (_, k) => ({ sampleId: 'chirp', start: 512 * k, end: 512 * k + 512 })) };
sliced.slices[1] = { sampleId: 'chirp', start: 256, end: 2000 };
project.drums[1] = sliced;

// Pattern 1: melodic run on Sound 1, Sound 2 and 3 notes, kit hits, a filter lock and a
// parameter-only lock. Pattern 2: the chirp slices in order with FX 1 on steps 9..12.
const p1 = project.patterns[0];
const p2 = project.patterns[1];
for (const [step, key] of [[1, 1], [5, 5], [9, 9], [13, 13]] as const) writeCell(p1, step, 1, { key, ...DEFAULT_PARAMETERS });
writeCell(p1, 9, 1, { key: 9, ...DEFAULT_PARAMETERS, filter: 20 });
writeCell(p1, 2, 1, { key: null, pitch: 0, volume: 20, filter: 0, resonance: 0 });
writeCell(p1, 3, 2, { key: 1, ...DEFAULT_PARAMETERS });
writeCell(p1, 11, 2, { key: 1, ...DEFAULT_PARAMETERS });
writeCell(p1, 7, 3, { key: 1, ...DEFAULT_PARAMETERS });
for (const [step, key] of [[1, 1], [9, 1], [5, 2], [13, 2], [3, 3], [7, 4], [11, 5], [15, 6]] as const) {
  writeCell(p1, step, 9, { key, ...DEFAULT_PARAMETERS });
}
for (let step = 1; step <= 16; step++) writeCell(p2, step, 10, { key: step, ...DEFAULT_PARAMETERS });
writeEffects(p2, [null, null, null, null, null, null, null, null, 1, 1, 1, 1, null, null, null, null]);

const state = compileProject(project, (id) => library.get(id)!, emptyTemplateState());
const packets = serializeState(state);
const body = encodePackets(packets);
const wav = encodeRestoreWav(labelsForBody(body));

mkdirSync(OUT, { recursive: true });
writeFileSync(resolve(OUT, 'restore.wav'), wav);
writeFileSync(
  resolve(OUT, 'packets.json'),
  JSON.stringify({ schema: 'sosample.packets', packets: packets.map((p) => ({ tag: p.tag, payload: bytesToBase64(p.payload) })) }),
);
writeFileSync(
  resolve(OUT, 'project.json'),
  JSON.stringify(
    {
      ...project,
      patterns: project.patterns.map(bytesToBase64),
      samples: Object.fromEntries([...library].map(([id, codes]) => [id, { codes: codes.length, base64: bytesToBase64(codes) }])),
    },
    null,
    1,
  ),
);
console.log(JSON.stringify({ pages: usedPages(state), packets: packets.length, bodyBytes: body.length, wavBytes: wav.length, seconds: (wav.length - 44) / 4 / 44100 }));
