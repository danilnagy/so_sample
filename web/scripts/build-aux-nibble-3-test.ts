/**
 * Build the restore for the registered aux-nibble-003 test (docs/aux-nibble-3-control.md):
 * do a drum's retrigger spacing and a melodic note's length follow the tempo, and what does
 * swing do to them? 120 BPM (a 125 ms step) with swing 12 (even steps 62.5 ms late).
 *
 * - Drum: a 6 ms click on Sound 9 key 1 with retriggers 2, 3, 4, 6 and 8, each on an odd and
 *   an even step (steps 1, 6, 9 and 14 of Patterns 1 to 3).
 * - Melodic: lengths 1, 2, 3 and 4 (Patterns 4 to 7), each on an odd step (step 1, Sound 1, a
 *   2 s 700 Hz tone) and an even step (step 2, Sound 2, a 2 s 1000 Hz tone): two sounds, so a
 *   note as long as a second can never meet the next note of its own sound.
 *
 * Writes restore.wav, packets.json and project.json into experiments/aux-nibble-003;
 * scripts/prepare_aux_nibble_3_test.py registers the test from those files.
 *
 *   npx tsx scripts/build-aux-nibble-3-test.ts      (from web/)
 */

import { resolve } from 'node:path';

import { type Clip, type Project, emptyProject } from '../src/core/project';
import { type Probe, type Written, click, compileAndWrite, tone, whole, writeProbe } from './aux-nibble-tools';

const OUT = resolve(import.meta.dirname, '../../experiments/aux-nibble-003');

export const TEMPO = 120;
export const SWING = 12;
export const STEP_SECONDS = 15 / TEMPO;
/** Even steps are delayed by swing / 24 of a step (swing-law-results.md). */
export const SWING_DELAY_SECONDS = (SWING / 24) * STEP_SECONDS;
export const CLICK = { sound: 9, key: 1, hz: 5000, seconds: 0.006, tau: 0.0012 };
export const TONE = { sound: 1, key: 5, hz: 700, seconds: 2 };
export const TONE_EVEN = { sound: 2, key: 5, hz: 1000, seconds: 2 };

const project: Project = emptyProject(TEMPO);
project.swing = SWING;
const library = new Map<string, Uint8Array>([
  ['click', click(CLICK.hz, CLICK.seconds, CLICK.tau)],
  ['tone', tone(TONE.hz, TONE.seconds)],
  ['toneEven', tone(TONE_EVEN.hz, TONE_EVEN.seconds)],
]);
project.melodic[TONE.sound - 1] = whole(library, 'tone');
project.melodic[TONE_EVEN.sound - 1] = whole(library, 'toneEven');
const slices: (Clip | null)[] = new Array(16).fill(null);
slices[CLICK.key - 1] = whole(library, 'click');
project.drums[CLICK.sound - 9] = { slices };

const drum = (pattern: number, step: number, nibble: number): Probe => ({ pattern, step, sound: CLICK.sound, key: CLICK.key, nibble });
const mel = (pattern: number, step: number, nibble: number): Probe => {
  const t = step % 2 === 0 ? TONE_EVEN : TONE;
  return { pattern, step, sound: t.sound, key: t.key, nibble };
};

/** Odd steps 1 and 9, even steps 6 and 14: each retrigger once on each parity. */
export const DRUM_PROBES = [
  drum(1, 1, 2),
  drum(1, 6, 2),
  drum(1, 9, 3),
  drum(1, 14, 3),
  drum(2, 1, 4),
  drum(2, 6, 4),
  drum(2, 9, 6),
  drum(2, 14, 6),
  drum(3, 1, 8),
  drum(3, 6, 8),
];
/** Step 1 (odd, Sound 1) and step 2 (even, Sound 2) of Patterns 4 to 7, lengths 1 to 4. */
export const MELODIC_PROBES = [1, 2, 3, 4].flatMap((n, i) => [mel(4 + i, 1, n), mel(4 + i, 2, n)]);
export const CHAIN = [1, 2, 3, 4, 5, 6, 7];
project.chain = CHAIN;

const written: Written[] = [...DRUM_PROBES, ...MELODIC_PROBES].map((p) => writeProbe(project, p));
const facts = compileAndWrite(OUT, project, library, written, [], {
  step_seconds: STEP_SECONDS,
  swing_delay_seconds: SWING_DELAY_SECONDS,
  click: CLICK,
  tone: TONE,
  tone_even: TONE_EVEN,
  drum_probes: DRUM_PROBES,
  melodic_probes: MELODIC_PROBES,
});
console.log(JSON.stringify(facts));
