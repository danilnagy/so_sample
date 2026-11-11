/**
 * Build the restore for the registered kit-sharing test (docs/kit-sharing-control.md):
 * drum sounds that reference samples stored in an earlier drum sound's kit buffer. Writes
 * restore.wav, packets.json and project.json into experiments/kit-sharing-001;
 * scripts/prepare_kit_sharing_test.py registers the test from those files.
 *
 *   npx tsx scripts/build-kit-sharing-test.ts      (from web/)
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { bytesToBase64 } from '../src/core/bytes';
import { labelsForBody } from '../src/core/labels';
import { encodeRestoreWav } from '../src/core/modem/encode';
import { encodeMulaw } from '../src/core/mulaw';
import { encodePackets } from '../src/core/packets';
import { DEFAULT_PARAMETERS, writeCell } from '../src/core/pattern';
import { type Clip, type Project, compileProject, drumSoundIds, emptyProject } from '../src/core/project';
import { serializeState, usedPages } from '../src/core/state';
import { emptyTemplateState } from '../src/core/template';

const RATE = 23437.5;
const OUT = resolve(import.meta.dirname, '../../experiments/kit-sharing-001');

/** Deterministic noise burst (linear congruential), decaying. */
function burst(seconds: number, peak: number, seed: number, decay: number): Uint8Array {
  const n = Math.round(seconds * RATE);
  const samples = new Float64Array(n);
  let x = seed >>> 0;
  for (let i = 0; i < n; i++) {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0;
    samples[i] = peak * ((x / 2 ** 32) * 2 - 1) * Math.exp(-i / (decay * n));
  }
  return encodeMulaw(samples);
}

/** A falling sine, the kick: 150 Hz sweeping to 50 Hz. */
function kick(seconds: number): Uint8Array {
  const n = Math.round(seconds * RATE);
  const samples = new Float64Array(n);
  let phase = 0;
  for (let i = 0; i < n; i++) {
    const hz = 50 + 100 * Math.exp(-i / (0.15 * n));
    phase += (2 * Math.PI * hz) / RATE;
    samples[i] = 0.8 * Math.sin(phase) * Math.exp(-i / (0.5 * n));
  }
  return encodeMulaw(samples);
}

/** A 900 Hz square blip, the clap stand-in: clearly unlike the other three. */
function blip(seconds: number): Uint8Array {
  const n = Math.round(seconds * RATE);
  const samples = new Float64Array(n);
  for (let i = 0; i < n; i++) samples[i] = 0.5 * Math.sign(Math.sin((2 * Math.PI * 900 * i) / RATE)) * Math.exp(-i / (0.4 * n));
  return encodeMulaw(samples);
}

export const library = new Map<string, Uint8Array>([
  ['kick', kick(0.25)],
  ['snare', burst(0.18, 0.6, 2, 0.3)],
  ['hat', burst(0.05, 0.4, 3, 0.2)],
  ['blip', blip(0.12)],
]);
const len = (id: string) => library.get(id)!.length;
const whole = (id: string): Clip => ({ sampleId: id, start: 0, end: len(id) });

const project: Project = emptyProject(100);
project.chain = [1, 2, 3];
// Sound 11: the kit that stores kick, snare and hat (keys 1, 3, 7).
const kitA = () => {
  const slices: (Clip | null)[] = new Array(16).fill(null);
  slices[0] = whole('kick');
  slices[2] = whole('snare');
  slices[6] = whole('hat');
  return { slices };
};
project.drums[2] = kitA();
// Sound 12: the same kit; every key references Sound 11's buffer and Sound 12 stores nothing.
project.drums[3] = kitA();
// Sound 13: a mixed kit. Key 1's kick and key 6's blip are stored in its own buffer (key 1
// always joins the buffer when one exists); keys 3 and 7 reference Sound 11's buffer; key 5
// references a window from part-way into Sound 11's snare.
const mixed = kitA();
mixed.slices[5] = whole('blip');
mixed.slices[4] = { sampleId: 'snare', start: 1500, end: len('snare') };
project.drums[4] = mixed;

const note = (pattern: number, step: number, sound: number, key: number) => writeCell(project.patterns[pattern - 1], step, sound, { key, ...DEFAULT_PARAMETERS });
// One beat for all three patterns: kick 1 and 9, snare 5 and 13, hats on the off-beats.
const beat = (pattern: number, sound: number) => {
  for (const step of [1, 9]) note(pattern, step, sound, 1);
  for (const step of [5, 13]) note(pattern, step, sound, 3);
  for (const step of [3, 7, 11, 15]) note(pattern, step, sound, 7);
};
beat(1, 11);
beat(2, 12);
beat(3, 13);
note(3, 14, 13, 6); // the blip after the last snare
note(3, 16, 13, 5); // the snare's tail on the last step

const state = compileProject(project, (id) => library.get(id)!, emptyTemplateState(), { shareKitSamples: true });

// The layout this test is about, asserted before anything is written.
const [a, b, c] = [drumSoundIds(11), drumSoundIds(12), drumSoundIds(13)];
const owners = (ids: number[], keys: number[]) => keys.map((k) => state.sounds[ids[k - 1]]!.owner);
const expect = (what: string, ok: boolean) => {
  if (!ok) throw new Error(`Unexpected layout: ${what}`);
};
expect('Sound 11 owns its buffer', owners(a, [1, 3, 7]).every((o) => o === a[0]) && state.sounds[a[0]]!.codes.length > 0);
expect('Sound 12 references Sound 11 on every key and stores nothing', owners(b, [1, 3, 7]).every((o) => o === a[0]) && state.sounds[b[0]]!.codes.length === 0);
expect('Sound 13 owns keys 1 and 6', owners(c, [1, 6]).every((o) => o === c[0]) && state.sounds[c[0]]!.codes.length > 0);
expect('Sound 13 references Sound 11 on keys 3, 5 and 7', owners(c, [3, 5, 7]).every((o) => o === a[0]));
const unshared = compileProject(project, (id) => library.get(id)!, emptyTemplateState());

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
      ...project,
      patterns: project.patterns.map(bytesToBase64),
      samples: Object.fromEntries([...library].map(([id, codes]) => [id, { codes: codes.length, base64: bytesToBase64(codes) }])),
      layout: Object.fromEntries(
        [11, 12, 13].flatMap((sound) =>
          drumSoundIds(sound)
            .map((id, k) => [id, k, state.sounds[id]] as const)
            .filter(([, , r]) => r)
            .map(([id, k, r]) => [`Sound ${sound} key ${k + 1}`, { id, owner: r!.owner, start: r!.start, end: r!.end, stores: r!.codes.length }]),
        ),
      ),
    },
    null,
    1,
  ),
);
console.log(JSON.stringify({ pages: usedPages(state), pagesUnshared: usedPages(unshared), packets: packets.length, bodyBytes: body.length, wavBytes: wav.length, seconds: (wav.length - 44) / 4 / 44100 }));
