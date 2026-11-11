/**
 * Build the restore for the registered aux-nibble test (docs/aux-nibble-control.md): does a
 * step's auxiliary high nibble hold a drum step's retrigger count and a melodic note's length?
 * Writes restore.wav, packets.json and project.json into experiments/aux-nibble-001;
 * scripts/prepare_aux_nibble_test.py registers the test from those files.
 *
 *   npx tsx scripts/build-aux-nibble-test.ts      (from web/)
 *
 * The app writes 0xF0 | (key - 1) for a melodic note and 0x10 | (key - 1) for a drum note.
 * This restore writes other high nibbles on purpose, as raw auxiliary bytes after the cell.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { bytesToBase64 } from '../src/core/bytes';
import { labelsForBody } from '../src/core/labels';
import { encodeRestoreWav } from '../src/core/modem/encode';
import { SAMPLE_RATE, encodeMulaw } from '../src/core/mulaw';
import { encodePackets } from '../src/core/packets';
import { DEFAULT_PARAMETERS, cellOffsets, readCell, writeCell } from '../src/core/pattern';
import { type Clip, type Project, compileProject, emptyProject } from '../src/core/project';
import { serializeState, usedPages } from '../src/core/state';
import { emptyTemplateState } from '../src/core/template';

const OUT = resolve(import.meta.dirname, '../../experiments/aux-nibble-001');

/** 60 BPM, the slowest tempo: a step is 250 ms, so eight repeats in a step are 31 ms apart. */
export const TEMPO = 60;
export const STEP_SECONDS = 15 / TEMPO;
/** The melodic tone: long enough that a length of up to 14 steps would end it early. */
export const TONE_HZ = 500;
export const TONE_SECONDS = 3;
/** The drum hit: a 4 ms burst at 3 kHz, so each repeat is a separate, sharp onset. */
export const CLICK_SECONDS = 0.012;

export const DRUM_SOUND = 9;
export const DRUM_KEY = 1;
export const MELODIC_SOUND = 1;
/** Key 5 plays a melodic sample at its own pitch. */
export const MELODIC_KEY = 5;

/**
 * The probes: one note per probe with the given high nibble. Drum probes sit eight steps
 * apart, so a retrigger lasting a whole step per count (up to eight steps) cannot reach the
 * next probe; each melodic probe has a pattern of its own (4 s), longer than the tone.
 */
export const DRUM_PROBES = [
  { pattern: 1, step: 1, nibble: 1 },
  { pattern: 1, step: 9, nibble: 2 },
  { pattern: 2, step: 1, nibble: 3 },
  { pattern: 2, step: 9, nibble: 4 },
  { pattern: 3, step: 1, nibble: 6 },
  { pattern: 3, step: 9, nibble: 8 },
  { pattern: 4, step: 1, nibble: 5 },
  { pattern: 4, step: 9, nibble: 7 },
];
export const MELODIC_PROBES = [
  { pattern: 5, step: 1, nibble: 0xf },
  { pattern: 6, step: 1, nibble: 1 },
  { pattern: 7, step: 1, nibble: 2 },
  { pattern: 8, step: 1, nibble: 4 },
  { pattern: 9, step: 1, nibble: 8 },
  { pattern: 10, step: 1, nibble: 0xe },
];
export const CHAIN = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

function tone(): Uint8Array {
  const n = Math.round(TONE_SECONDS * SAMPLE_RATE);
  const fade = Math.round(0.01 * SAMPLE_RATE);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) out[i] = 0.7 * Math.sin((2 * Math.PI * TONE_HZ * i) / SAMPLE_RATE) * Math.min(1, i / fade, (n - i) / fade);
  return encodeMulaw(out);
}

function click(): Uint8Array {
  const n = Math.round(CLICK_SECONDS * SAMPLE_RATE);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) out[i] = 0.9 * Math.sin((2 * Math.PI * 3000 * i) / SAMPLE_RATE) * Math.exp(-i / (0.004 * SAMPLE_RATE));
  return encodeMulaw(out);
}

const library = new Map<string, Uint8Array>([
  ['tone', tone()],
  ['click', click()],
]);
const whole = (id: string): Clip => ({ sampleId: id, start: 0, end: library.get(id)!.length });

const project: Project = emptyProject(TEMPO);
project.chain = CHAIN;
project.melodic[MELODIC_SOUND - 1] = whole('tone');
const slices: (Clip | null)[] = new Array(16).fill(null);
slices[DRUM_KEY - 1] = whole('click');
project.drums[DRUM_SOUND - 9] = { slices };

/** A note, then its auxiliary byte rewritten with the probe's high nibble and the key in the low one. */
function probe(pattern: number, step: number, sound: number, key: number, nibble: number): number {
  const data = project.patterns[pattern - 1];
  writeCell(data, step, sound, { key, ...DEFAULT_PARAMETERS });
  const { aux } = cellOffsets(step, sound);
  data[aux] = (nibble << 4) | (key - 1);
  return aux;
}

const written: { pattern: number; step: number; sound: number; key: number; nibble: number; aux: number; byte: number }[] = [];
for (const p of DRUM_PROBES) written.push({ ...p, sound: DRUM_SOUND, key: DRUM_KEY, aux: probe(p.pattern, p.step, DRUM_SOUND, DRUM_KEY, p.nibble), byte: (p.nibble << 4) | (DRUM_KEY - 1) });
for (const p of MELODIC_PROBES) written.push({ ...p, sound: MELODIC_SOUND, key: MELODIC_KEY, aux: probe(p.pattern, p.step, MELODIC_SOUND, MELODIC_KEY, p.nibble), byte: (p.nibble << 4) | (MELODIC_KEY - 1) });

const state = compileProject(project, (id) => library.get(id)!, emptyTemplateState());

// The layout this test is about, asserted before anything is written: every probe's byte
// reaches the compiled pattern as written, still reads as the right key, and no other cell
// holds a note.
const expect = (what: string, ok: boolean) => {
  if (!ok) throw new Error(`Unexpected layout: ${what}`);
};
for (const w of written) {
  const data = state.patterns[w.pattern - 1];
  expect(`pattern ${w.pattern} step ${w.step} sound ${w.sound} aux byte`, data[w.aux] === w.byte);
  expect(`pattern ${w.pattern} step ${w.step} sound ${w.sound} key`, readCell(data, w.step, w.sound)?.key === w.key);
}
let notes = 0;
state.patterns.forEach((data) => {
  for (let step = 1; step <= 16; step++) for (let sound = 1; sound <= 16; sound++) if (readCell(data, step, sound)?.key) notes++;
});
expect('one note per probe and no others', notes === written.length);

const packets = serializeState(state);
const body = encodePackets(packets);
const wav = encodeRestoreWav(labelsForBody(body));
mkdirSync(OUT, { recursive: true });
writeFileSync(resolve(OUT, 'restore.wav'), wav);
writeFileSync(resolve(OUT, 'packets.json'), JSON.stringify({ schema: 'sosample.packets', packets: packets.map((p) => ({ tag: p.tag, payload: bytesToBase64(p.payload) })) }));
writeFileSync(
  resolve(OUT, 'project.json'),
  JSON.stringify(
    {
      tempo: TEMPO,
      swing: 0,
      chain: CHAIN,
      step_seconds: STEP_SECONDS,
      tone: { sound: MELODIC_SOUND, key: MELODIC_KEY, hz: TONE_HZ, seconds: TONE_SECONDS, codes: library.get('tone')!.length },
      click: { sound: DRUM_SOUND, key: DRUM_KEY, hz: 3000, seconds: CLICK_SECONDS, codes: library.get('click')!.length },
      drum_probes: DRUM_PROBES,
      melodic_probes: MELODIC_PROBES,
      aux_bytes: written.map((w) => ({ pattern: w.pattern, step: w.step, sound: w.sound, offset: w.aux, byte: w.byte })),
      patterns: project.patterns.map(bytesToBase64),
      samples: Object.fromEntries([...library].map(([id, codes]) => [id, { codes: codes.length, base64: bytesToBase64(codes) }])),
    },
    null,
    1,
  ),
);
console.log(JSON.stringify({ pages: usedPages(state), packets: packets.length, bodyBytes: body.length, wavBytes: wav.length, seconds: (wav.length - 44) / 4 / 44100 }));
