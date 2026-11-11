/**
 * Build the lofi project packs (<name>.sosample.zip) that import into the app.
 *
 *   npx tsx scripts/make-lofi-packs.ts "<TR pack folder>" "<output folder>"
 *
 * Each pack is a full project: Rhodes-style chord samples (one voicing per chord type,
 * transposed by the keys), a bass and a lead synthesized with a vinyl texture baked in,
 * drums picked from the Roland TR packs, patterns sequenced into a song chain, with the
 * lofi colour written as filter and volume locks on the notes. Every pattern is checked
 * against the device's four voices and the project against its 241 pages.
 *
 * Sound layout: 1 min7 chords, 2 dom7 chords, 3 maj7 chords, 4 bass, 5 lead, 6 a second
 * min7 voicing; 11 kick, 12 snare and rim, 13 hats, 14 percussion. Sounds 9 and 10 stay
 * empty: the device gives them the lowest voice priority.
 */

import { mkdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

import { type Colour, D, type Note, type SongSpec, mustKey, rhodesChord, rhodesLead, subBass, writePack } from './pack-tools';

const COLOUR: Record<number, Colour> = {
  1: { volume: 30, filter: 22 },
  2: { volume: 30, filter: 22 },
  3: { volume: 30, filter: 22 },
  4: { volume: 40, filter: 17 },
  5: { volume: 32, filter: 25 },
  6: { volume: 30, filter: 22 },
  11: { volume: 44, filter: 20 },
  12: { volume: 36, filter: 23 },
  13: { volume: 24, filter: 26 },
  14: { volume: 26, filter: 24 },
};

/** The keys a pack's grooves use, on the standard kits of sounds 11 (kicks), 12 (snares), 13 (hats) and 14 (percussion). */
interface Keys {
  kick: number;
  kick2: number;
  snare: number;
  rim: number;
  clap: number;
  ch: number;
  oh: number;
  shaker: number;
  perc1: number;
  perc2: number;
}

type Grooves = Record<'main' | 'fill' | 'sparse' | 'half' | 'halfFill', () => Note[]>;

/** Drum grooves on the four drum sounds. */
const groovesFor = (K: Keys): Grooves => ({
  /** The main lofi groove: lazy kick, snare on 2 and 4, eighth hats with the offbeats quieter. */
  main: () => [
    { step: 1, sound: 11, key: K.kick },
    { step: 8, sound: 11, key: K.kick, volume: 38 },
    { step: 11, sound: 11, key: K.kick },
    { step: 5, sound: 12, key: K.snare },
    { step: 13, sound: 12, key: K.snare },
    ...[1, 3, 5, 7, 9, 11, 13, 15].map((step) => ({ step, sound: 13, key: K.ch, volume: step % 4 === 1 ? 26 : 20 })),
    { step: 14, sound: 13, key: K.ch, volume: 16 },
  ],
  /** The groove with a fill: rim on the last beat and an open hat before the turn. */
  fill: () => [
    { step: 1, sound: 11, key: K.kick },
    { step: 8, sound: 11, key: K.kick, volume: 38 },
    { step: 11, sound: 11, key: K.kick },
    { step: 5, sound: 12, key: K.snare },
    { step: 13, sound: 12, key: K.snare },
    { step: 16, sound: 12, key: K.rim, volume: 30 },
    ...[1, 3, 5, 7, 9, 11, 13].map((step) => ({ step, sound: 13, key: K.ch, volume: step % 4 === 1 ? 26 : 20 })),
    { step: 14, sound: 13, key: K.oh, volume: 24 },
  ],
  /** Under the melody: hats on the beats only, so the lead has a voice. */
  sparse: () => [
    { step: 1, sound: 11, key: K.kick },
    { step: 8, sound: 11, key: K.kick, volume: 38 },
    { step: 11, sound: 11, key: K.kick },
    { step: 5, sound: 12, key: K.snare },
    { step: 13, sound: 12, key: K.snare },
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 13, key: K.ch, volume: 24 })),
  ],
  /** Half time: the 808 on 1 and the "and" of 3, snare on 3, sixteenth shaker. */
  half: () => [
    { step: 1, sound: 11, key: K.kick2 },
    { step: 12, sound: 11, key: K.kick2, volume: 36 },
    { step: 9, sound: 12, key: K.snare },
    ...[3, 7, 11, 15].map((step) => ({ step, sound: 13, key: K.shaker, volume: 22 })),
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 13, key: K.ch, volume: 24 })),
  ],
  /** Half time with the rim and a conga answer. */
  halfFill: () => [
    { step: 1, sound: 11, key: K.kick2 },
    { step: 12, sound: 11, key: K.kick2, volume: 36 },
    { step: 9, sound: 12, key: K.snare },
    { step: 15, sound: 12, key: K.rim, volume: 28 },
    ...[3, 7, 11].map((step) => ({ step, sound: 13, key: K.shaker, volume: 22 })),
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 13, key: K.ch, volume: 24 })),
    { step: 14, sound: 14, key: K.perc1, volume: 26 },
    { step: 16, sound: 14, key: K.perc2, volume: 22 },
  ],
});

/** The lofi trims: the 808 and the open hat kept shorter than the kits' caps, so the chords keep their voices. */
const LOFI_TRIMS = {
  kicks: { [D.kick]: 0.3, [D.kick2]: 0.45 },
  snares: { [D.snare]: 0.3, [D.rim]: 0.15, [D.clap]: 0.3 },
  hats: { [D.ch]: 0.12, [D.ch2]: 0.15, [D.oh]: 0.4 },
};

interface Bar {
  chord: [number, number];
  bass: number;
  groove: keyof Grooves;
  chordAgain?: boolean;
  lead?: [number, number, number?][];
}

/** A bar: the chord on 1 (and again on beat 3, quieter, when asked), bass on 1, 8 and 11, the groove and the lead notes. */
function bar(g: Grooves, b: Bar): Note[] {
  const notes: Note[] = [
    { step: 1, sound: b.chord[0], key: b.chord[1] },
    { step: 1, sound: 4, key: b.bass },
    { step: 8, sound: 4, key: b.bass, volume: 30 },
    { step: 11, sound: 4, key: b.bass, volume: 34 },
    ...g[b.groove](),
  ];
  if (b.chordAgain) notes.push({ step: 9, sound: b.chord[0], key: b.chord[1], volume: 22 });
  for (const [step, key, volume] of b.lead ?? []) notes.push({ step, sound: 5, key, volume });
  return notes;
}

// Under eight steps at these tempos, so a bar's chord has ended before the next one and the lead need a voice.
const CHORD = 1.4;
// Under three steps, so melody notes three steps apart never stack two voices.
const LEAD = 0.5;

export function rainyRhodes(): SongSpec {
  // F major, ii V I vi. Chord sounds: min7 at G, dom7 at C, maj7 at F, a second min7 at D; bass at D2; lead at A4.
  const Gm: [number, number] = [1, mustKey(0, 'Gm7')];
  const C7: [number, number] = [2, mustKey(0, 'C7')];
  const F: [number, number] = [3, mustKey(0, 'Fmaj7')];
  const Dm: [number, number] = [6, mustKey(0, 'Dm7')];
  const Bb: [number, number] = [3, mustKey(5, 'Bbmaj7')];
  const bG = mustKey(5, 'bass G');
  const bC = mustKey(-2, 'bass C');
  const bF = mustKey(3, 'bass F');
  const bD = mustKey(0, 'bass D');
  const bBb = mustKey(8, 'bass Bb');
  // Lead at A4: F -4, G -2, A 0, C +3, D +5, E +7, F +8, G +10.
  const L = { F: mustKey(-4, 'F'), G: mustKey(-2, 'G'), A: mustKey(0, 'A'), C: mustKey(3, 'C'), D: mustKey(5, 'D'), E: mustKey(7, 'E'), F5: mustKey(8, 'F5'), G5: mustKey(10, 'G5') };
  const g = groovesFor({ kick: D.kick, kick2: D.kick2, snare: D.snare, rim: D.rim, clap: D.clap, ch: D.ch, oh: D.oh, shaker: D.ch2, perc1: 9, perc2: 11 });
  return {
    name: 'Rainy Rhodes',
    tempo: 84,
    swing: 7,
    melodic: {
      1: { id: 'min7', name: 'min7 rhodes', samples: rhodesChord([55, 58, 62, 65, 69], CHORD, 12) },
      2: { id: 'dom7', name: 'dom7 rhodes', samples: rhodesChord([52, 58, 60, 64, 67], CHORD, 13) },
      3: { id: 'maj7', name: 'maj7 rhodes', samples: rhodesChord([53, 57, 60, 64, 67], CHORD, 14) },
      4: { id: 'bass', name: 'bass', samples: subBass(38, 0.5) },
      5: { id: 'lead', name: 'lead rhodes', samples: rhodesLead(69, LEAD, 15) },
      6: { id: 'min7b', name: 'min7 rhodes II', samples: rhodesChord([50, 53, 57, 60, 64], CHORD, 16) },
    },
    // Kicks from the 808, snares from the 707, hats and shaker from the 626, congas from the 808 percussion kit.
    kits: {
      11: { kit: 'TR-808', trim: LOFI_TRIMS.kicks },
      12: { kit: 'TR-707', trim: LOFI_TRIMS.snares },
      13: { kit: 'TR-626', trim: LOFI_TRIMS.hats },
      14: { kit: 'TR-808 Percussion', trim: { 9: 0.25, 11: 0.25 } },
    },
    colour: COLOUR,
    bars: [
      bar(g, { chord: Gm, bass: bG, groove: 'main' }),
      bar(g, { chord: C7, bass: bC, groove: 'main' }),
      bar(g, { chord: F, bass: bF, groove: 'main' }),
      bar(g, { chord: Dm, bass: bD, groove: 'fill' }),
      bar(g, { chord: Gm, bass: bG, groove: 'sparse', lead: [[3, L.D], [7, L.C], [11, L.A, 28]] }),
      bar(g, { chord: C7, bass: bC, groove: 'sparse', lead: [[2, L.E], [6, L.D], [10, L.C, 28], [13, L.G, 26]] }),
      bar(g, { chord: F, bass: bF, groove: 'sparse', lead: [[3, L.A], [7, L.C], [12, L.F5, 30]] }),
      bar(g, { chord: Dm, bass: bD, groove: 'sparse', lead: [[2, L.E], [5, L.D], [9, L.F, 28], [13, L.G5, 26]] }),
      bar(g, { chord: Bb, bass: bBb, groove: 'main', chordAgain: true }),
      bar(g, { chord: C7, bass: bC, groove: 'main', chordAgain: true }),
      bar(g, { chord: F, bass: bF, groove: 'main', chordAgain: true }),
      bar(g, { chord: Dm, bass: bD, groove: 'fill', chordAgain: true }),
    ],
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 9, 10, 11, 12, 9, 10, 11, 12, 1, 2, 3, 4],
  };
}

export function nightWalk(): SongSpec {
  // D minor, half time, i iv VI V. Chord sounds: min7 at D, dom7 at A, maj7 at Bb; bass at D2; lead at D5.
  const Dm: [number, number] = [1, mustKey(0, 'Dm7')];
  const Gm: [number, number] = [1, mustKey(5, 'Gm7')];
  const Bb: [number, number] = [3, mustKey(0, 'Bbmaj7')];
  const A7: [number, number] = [2, mustKey(0, 'A7')];
  const bD = mustKey(0, 'bass D');
  const bG = mustKey(5, 'bass G');
  const bBb = mustKey(8, 'bass Bb');
  const bA = mustKey(7, 'bass A');
  // Lead at D5: A4 -5, C5 -2, D5 0, E5 +2, F5 +3, G5 +5, A5 +7.
  const L = { A: mustKey(-5, 'A'), C: mustKey(-2, 'C'), D: mustKey(0, 'D'), E: mustKey(2, 'E'), F: mustKey(3, 'F'), G: mustKey(5, 'G'), A5: mustKey(7, 'A5') };
  const g = groovesFor({ kick: D.kick, kick2: D.kick2, snare: D.snare, rim: D.rim, clap: D.clap, ch: D.ch, oh: D.oh, shaker: D.ch2, perc1: 10, perc2: 5 });
  return {
    name: 'Night Walk',
    tempo: 76,
    swing: 9,
    melodic: {
      1: { id: 'min7', name: 'min7 rhodes', samples: rhodesChord([50, 53, 57, 60, 64], CHORD, 24) },
      2: { id: 'dom7', name: 'dom7 rhodes', samples: rhodesChord([49, 55, 57, 61, 64], CHORD, 25) },
      3: { id: 'maj7', name: 'maj7 rhodes', samples: rhodesChord([46, 50, 53, 57, 60], CHORD, 26) },
      4: { id: 'bass', name: 'bass', samples: subBass(38, 0.55) },
      5: { id: 'lead', name: 'lead rhodes', samples: rhodesLead(74, LEAD, 27) },
    },
    // Kicks and snares from the 909 (its second kick stands in for the 808), hats from the 808, conga and clave from the 808 percussion kit.
    kits: {
      11: { kit: 'TR-909', trim: LOFI_TRIMS.kicks },
      12: { kit: 'TR-909', trim: LOFI_TRIMS.snares },
      13: { kit: 'TR-808', trim: LOFI_TRIMS.hats },
      14: { kit: 'TR-808 Percussion', trim: { 10: 0.25, 5: 0.25 } },
    },
    colour: COLOUR,
    bars: [
      bar(g, { chord: Dm, bass: bD, groove: 'half' }),
      bar(g, { chord: Gm, bass: bG, groove: 'half' }),
      bar(g, { chord: Bb, bass: bBb, groove: 'half' }),
      bar(g, { chord: A7, bass: bA, groove: 'halfFill' }),
      bar(g, { chord: Dm, bass: bD, groove: 'half', lead: [[3, L.F], [7, L.E], [11, L.D, 28]] }),
      bar(g, { chord: Gm, bass: bG, groove: 'half', lead: [[2, L.G], [6, L.F], [10, L.D, 28]] }),
      bar(g, { chord: Bb, bass: bBb, groove: 'half', lead: [[3, L.D], [7, L.F], [12, L.A5, 30]] }),
      bar(g, { chord: A7, bass: bA, groove: 'halfFill', lead: [[2, L.E], [6, L.C, 28], [10, L.A, 26]] }),
    ],
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 1, 2, 3, 4],
  };
}

async function main(): Promise<void> {
  const [pack, out] = process.argv.slice(2);
  if (!pack || !out) throw new Error('usage: make-lofi-packs.ts <TR pack folder> <output folder>');
  mkdirSync(out, { recursive: true });
  for (const spec of [rainyRhodes(), nightWalk()]) console.log((await writePack(spec, pack, out)).description);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error((error as Error).message);
    process.exit(1);
  });
}
