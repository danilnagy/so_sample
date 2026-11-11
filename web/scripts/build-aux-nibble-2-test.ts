/**
 * Build the restore for the registered aux-nibble-002 test (docs/aux-nibble-2-control.md):
 * what aux-nibble-001 left open, at 60 BPM with no swing.
 *
 * - Voices: a drum retrigger of 4, with 0, 1, 2 or 3 other voices held by long melodic notes.
 *   Whether the repeats share one voice or need one each shows in how many are heard.
 * - Choke: the same drum's body is decaying noise, so a repeat that restarts its voice leaves
 *   the level after it like a single hit's, and repeats that overlap add up in power.
 * - Melodic length for the nibbles not yet measured: 3, 5, 6, 7, 9, A, B, C, D, E and F, on
 *   5 s tones.
 * - Exploratory: FX 13 and FX 14 over a retriggered drum note and a shortened melodic note.
 *
 * Writes restore.wav, packets.json and project.json into experiments/aux-nibble-002;
 * scripts/prepare_aux_nibble_2_test.py registers the test from those files.
 *
 *   npx tsx scripts/build-aux-nibble-2-test.ts      (from web/)
 */

import { resolve } from 'node:path';

import { writeEffects } from '../src/core/pattern';
import { type Clip, type Project, emptyProject } from '../src/core/project';
import { type Probe, type Written, compileAndWrite, strike, tone, whole, writeProbe } from './aux-nibble-tools';

const OUT = resolve(import.meta.dirname, '../../experiments/aux-nibble-002');

export const TEMPO = 60;
export const STEP_SECONDS = 15 / TEMPO;

/** The drum: Sound 9 key 1, a 7 kHz click onset and a 1 s noise body around 3 kHz. */
export const DRUM = { sound: 9, key: 1, clickHz: 7000, bodyHz: 3000, bodyTau: 0.35, seconds: 1.0 };
/** Three holders, Sounds 1 to 3: 2.5 s tones, played for eight steps (2 s, nibble 8). */
export const HOLDERS = [
  { sound: 1, hz: 250 },
  { sound: 2, hz: 350 },
  { sound: 3, hz: 500 },
];
export const HOLDER_SECONDS = 2.5;
export const HOLDER_NIBBLE = 8;
/** The length probes: Sounds 5 and 6, 5 s tones at 700 Hz and 1000 Hz. */
export const MEL_A = { sound: 5, hz: 700 };
export const MEL_B = { sound: 6, hz: 1000 };
export const MEL_SECONDS = 5;
/** Key 5 plays a melodic sample at its own pitch. */
const KEY = 5;

const project: Project = emptyProject(TEMPO);
const library = new Map<string, Uint8Array>([
  ['strike', strike(DRUM.clickHz, DRUM.bodyHz, DRUM.bodyTau, DRUM.seconds)],
  ...HOLDERS.map((h) => [`holder${h.sound}`, tone(h.hz, HOLDER_SECONDS)] as [string, Uint8Array]),
  ['melA', tone(MEL_A.hz, MEL_SECONDS)],
  ['melB', tone(MEL_B.hz, MEL_SECONDS)],
]);
for (const h of HOLDERS) project.melodic[h.sound - 1] = whole(library, `holder${h.sound}`);
project.melodic[MEL_A.sound - 1] = whole(library, 'melA');
project.melodic[MEL_B.sound - 1] = whole(library, 'melB');
const slices: (Clip | null)[] = new Array(16).fill(null);
slices[DRUM.key - 1] = whole(library, 'strike');
project.drums[DRUM.sound - 9] = { slices };

const drum = (pattern: number, step: number, nibble: number): Probe => ({ pattern, step, sound: DRUM.sound, key: DRUM.key, nibble });
const mel = (pattern: number, s: { sound: number }, nibble: number): Probe => ({ pattern, step: 1, sound: s.sound, key: KEY, nibble });

/** Pattern 1: the single-hit reference (step 1) and the retrigger of 4 alone (step 9). */
export const REFERENCE = drum(1, 1, 1);
export const VOICE_PROBES = [
  { held: 0, probe: drum(1, 9, 4) },
  { held: 1, probe: drum(2, 5, 4) },
  { held: 2, probe: drum(3, 5, 4) },
  { held: 3, probe: drum(4, 5, 4) },
];
/** Patterns 2 to 4: 1, 2, 3 holders on step 1, a second before the drum. */
export const HOLDER_PROBES = [2, 3, 4].flatMap((pattern, i) => HOLDERS.slice(0, i + 1).map((h) => mel(pattern, h, HOLDER_NIBBLE)));
/** Patterns 5 to 8, exploratory: FX 13 and FX 14 over a retrigger of 4 and a two-step note. */
export const FX_PATTERNS = [
  { pattern: 5, fx: 13, held: [1, 8], probe: drum(5, 1, 4) },
  { pattern: 6, fx: 14, held: [5, 12], probe: drum(6, 1, 4) },
  { pattern: 7, fx: 13, held: [1, 8], probe: mel(7, MEL_A, 2) },
  { pattern: 8, fx: 14, held: [5, 12], probe: mel(8, MEL_A, 2) },
];
/** Patterns 9 to 14: the lengths, two probes a pattern (A and B) and F alone, last. */
export const LENGTH_PROBES = [
  mel(9, MEL_A, 3),
  mel(9, MEL_B, 5),
  mel(10, MEL_A, 6),
  mel(10, MEL_B, 7),
  mel(11, MEL_A, 9),
  mel(11, MEL_B, 0xa),
  mel(12, MEL_A, 0xb),
  mel(12, MEL_B, 0xc),
  mel(13, MEL_A, 0xd),
  mel(13, MEL_B, 0xe),
  mel(14, MEL_A, 0xf),
];
export const CHAIN = Array.from({ length: 14 }, (_, i) => i + 1);
project.chain = CHAIN;

const written: Written[] = [];
for (const p of [REFERENCE, ...VOICE_PROBES.map((v) => v.probe), ...HOLDER_PROBES, ...FX_PATTERNS.map((f) => f.probe), ...LENGTH_PROBES]) written.push(writeProbe(project, p));
const effects = FX_PATTERNS.map((f) => {
  const fx: (number | null)[] = Array.from({ length: 16 }, (_, i) => (i + 1 >= f.held[0] && i + 1 <= f.held[1] ? f.fx : null));
  writeEffects(project.patterns[f.pattern - 1], fx);
  return { pattern: f.pattern, effects: fx };
});

const facts = compileAndWrite(OUT, project, library, written, effects, {
  step_seconds: STEP_SECONDS,
  drum: DRUM,
  holders: HOLDERS,
  holder_seconds: HOLDER_SECONDS,
  holder_nibble: HOLDER_NIBBLE,
  melodic: { a: MEL_A, b: MEL_B, seconds: MEL_SECONDS, key: KEY },
  reference: REFERENCE,
  voice_probes: VOICE_PROBES,
  holder_probes: HOLDER_PROBES,
  fx_patterns: FX_PATTERNS,
  length_probes: LENGTH_PROBES,
});
console.log(JSON.stringify(facts));
