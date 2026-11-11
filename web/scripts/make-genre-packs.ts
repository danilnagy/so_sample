/**
 * Build the boom bap and house project packs (<name>.sosample.zip).
 *
 *   npx tsx scripts/make-genre-packs.ts "<TR pack folder>" "<output folder>"
 *
 * Two soul-driven boom bap songs (organ and Rhodes chords, brass stabs, a sub bass, hard
 * drums with swing) and two house songs: Chicago (piano stabs, a sawtooth bass on the
 * offbeats, 909 drums with the open hat on the "and") and Detroit (detuned string pads,
 * a sixteenth bassline, a bleep hook). Same layout as the lofi packs: chords on 1 to 3
 * (6 spare), bass on 4, lead on 5, drums on 11 to 14; every song is checked against the
 * four voices and the 241 pages.
 */

import { mkdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

import { type Colour, D, type Note, type SongSpec, bleep, brassStab, houseBass, mustKey, organChord, pianoStab, rhodesChord, rhodesLead, stringPad, subBass, writePack } from './pack-tools';

const K = (semitones: number, what: string): number => mustKey(semitones, what);

// Boom bap

const BOOM_COLOUR: Record<number, Colour> = {
  1: { volume: 30, filter: 24 },
  2: { volume: 28, filter: 23 },
  3: { volume: 30, filter: 26 },
  4: { volume: 42, filter: 16 },
  5: { volume: 30, filter: 25 },
  11: { volume: 46, filter: 63 },
  12: { volume: 42, filter: 63 },
  13: { volume: 24, filter: 28 },
  14: { volume: 28, filter: 28 },
};

/** Boom bap grooves on the standard kits: kicks on 11, snare, rim and clap on 12, hats on 13 (the second closed hat stands in for a shaker), tambourine (key 10) and cowbell (16) on the 626 on 14. */
const boom = {
  /** The head-nod: kick on 1, the "and" of 2 and the "and" of 3, snare on 2 and 4, eighth hats, a ghost sixteenth. */
  main: (): Note[] => [
    { step: 1, sound: 11, key: D.kick },
    { step: 8, sound: 11, key: D.kick, volume: 40 },
    { step: 11, sound: 11, key: D.kick },
    { step: 5, sound: 12, key: D.snare },
    { step: 13, sound: 12, key: D.snare },
    ...[1, 3, 5, 7, 9, 11, 13, 15].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 1 ? 26 : 20 })),
    { step: 16, sound: 13, key: D.ch, volume: 16 },
  ],
  /** The turnaround: the clap doubles the last snare, the rim answers, an open hat on the pickup. */
  turn: (): Note[] => [
    { step: 1, sound: 11, key: D.kick },
    { step: 8, sound: 11, key: D.kick, volume: 40 },
    { step: 11, sound: 11, key: D.kick },
    { step: 5, sound: 12, key: D.snare },
    { step: 13, sound: 12, key: D.clap },
    { step: 15, sound: 12, key: D.rim, volume: 30 },
    ...[1, 3, 5, 7, 9, 11, 13].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 1 ? 26 : 20 })),
    { step: 14, sound: 13, key: D.oh, volume: 22 },
  ],
  /** Under the melody: hats on the beats, the tambourine on the backbeat. */
  sparse: (): Note[] => [
    { step: 1, sound: 11, key: D.kick },
    { step: 8, sound: 11, key: D.kick, volume: 40 },
    { step: 11, sound: 11, key: D.kick },
    { step: 5, sound: 12, key: D.snare },
    { step: 13, sound: 12, key: D.snare },
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 13, key: D.ch, volume: 24 })),
  ],
};

/** The boom bap trims: hits kept as short as the grooves were tuned for. */
const BOOM_TRIMS = {
  kicks: { [D.kick]: 0.3, [D.kick2]: 0.3 },
  snares: { [D.snare]: 0.28, [D.rim]: 0.15, [D.clap]: 0.3 },
  hats: { [D.ch]: 0.12, [D.ch2]: 0.15, [D.oh]: 0.35 },
  perc: { 10: 0.2, 16: 0.2 },
};

/** Bass notes at the steps on the key, the first louder. */
const b = {
  bassNotes: (steps: number[], key: number): Note[] => steps.map((step, i) => ({ step, sound: 4, key, volume: i ? 32 : 42 })),
};

export function cornerStore(): SongSpec {
  // A minor soul: Am9 | Dm9 | Fmaj7 | E7. Organ min9 at A (Dm9 is +5), Rhodes maj7 at F, brass dom7 at E; bass at A1; lead at E5.
  const Am: [number, number] = [1, K(0, 'Am9')];
  const Dm: [number, number] = [1, K(5, 'Dm9')];
  const F: [number, number] = [2, K(0, 'Fmaj7')];
  const E7 = K(0, 'E7');
  const bA = K(0, 'bass A');
  const bD = K(5, 'bass D');
  const bF = K(8, 'bass F');
  const bE = K(7, 'bass E');
  // Lead at E5: A4 -7, C5 -4, D5 -2, E5 0, G5 +3, A5 +5.
  const L = { A: K(-7, 'A'), C: K(-4, 'C'), D: K(-2, 'D'), E: K(0, 'E'), G: K(3, 'G'), A5: K(5, 'A5') };
  const bar = (chord: [number, number], bassKey: number, groove: keyof typeof boom, extra: { chops?: number[]; lead?: [number, number, number?][] } = {}): Note[] => [
    { step: 1, sound: chord[0], key: chord[1] },
    ...(extra.chops ?? []).map((step) => ({ step, sound: chord[0], key: chord[1], volume: 24 })),
    ...b.bassNotes([1, 7, 11], bassKey),
    ...boom[groove](),
    ...(extra.lead ?? []).map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  const stabBar = (groove: keyof typeof boom, lead: [number, number, number?][] = []): Note[] => [
    ...b.bassNotes([1, 7, 11], bE),
    ...boom[groove](),
    ...[1, 4, 7, 10, 13].map((step, i) => ({ step, sound: 3, key: E7, volume: i % 2 ? 26 : 30 })),
    ...lead.map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  return {
    name: 'Corner Store',
    tempo: 92,
    swing: 9,
    melodic: {
      1: { id: 'min9', name: 'organ min9', samples: organChord([57, 60, 64, 67, 71], 0.9, 31) },
      2: { id: 'maj7', name: 'rhodes maj7', samples: rhodesChord([53, 57, 60, 64, 67], 1.0, 32) },
      3: { id: 'dom7', name: 'brass dom7', samples: brassStab([52, 56, 59, 62], 0.35) },
      4: { id: 'bass', name: 'sub bass', samples: subBass(33, 0.5) },
      5: { id: 'lead', name: 'lead rhodes', samples: rhodesLead(76, 0.45, 33) },
    },
    // An 808 kick, a 909 snare and clap, 707 hats, 626 tambourine and cowbell.
    kits: {
      11: { kit: 'TR-808', trim: BOOM_TRIMS.kicks },
      12: { kit: 'TR-909', trim: BOOM_TRIMS.snares },
      13: { kit: 'TR-707', trim: BOOM_TRIMS.hats },
      14: { kit: 'TR-626', trim: BOOM_TRIMS.perc },
    },
    colour: BOOM_COLOUR,
    bars: [
      bar(Am, bA, 'main', { chops: [7] }),
      bar(Dm, bD, 'main', { chops: [7] }),
      bar(F, bF, 'main', { chops: [7] }),
      stabBar('turn'),
      bar(Am, bA, 'sparse', { lead: [[3, L.E], [7, L.G], [11, L.E, 26], [14, L.D, 24]] }),
      bar(Dm, bD, 'sparse', { lead: [[2, L.A5], [6, L.G], [10, L.E, 26]] }),
      bar(F, bF, 'sparse', { lead: [[3, L.C], [7, L.D], [11, L.E, 26], [14, L.G, 24]] }),
      stabBar('sparse', [[2, L.E], [6, L.D], [10, L.C, 26]]),
    ],
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 1, 2, 3, 4],
  };
}

export function dustyCrates(): SongSpec {
  // C minor soul: Cm9 | Fm9 | Abmaj7 | G7. Organ min9 at C (Fm9 is +5), Rhodes maj7 at Ab, brass dom7 at G; bass at C2; lead at G4.
  const Cm: [number, number] = [1, K(0, 'Cm9')];
  const Fm: [number, number] = [1, K(5, 'Fm9')];
  const Ab: [number, number] = [2, K(0, 'Abmaj7')];
  const G7 = K(0, 'G7');
  const bC = K(0, 'bass C');
  const bF = K(5, 'bass F');
  const bAb = K(8, 'bass Ab');
  const bG = K(7, 'bass G');
  // Lead at G4: D4 -5, Eb4 -4, G4 0, Bb4 +3, C5 +5, D5 +7, Eb5 +8, F5 +10.
  const L = { D4: K(-5, 'D4'), Eb4: K(-4, 'Eb4'), G: K(0, 'G'), Bb: K(3, 'Bb'), C: K(5, 'C'), D: K(7, 'D'), Eb: K(8, 'Eb'), F: K(10, 'F') };
  const bar = (chord: [number, number], bassKey: number, groove: keyof typeof boom, extra: { chops?: number[]; lead?: [number, number, number?][] } = {}): Note[] => [
    { step: 1, sound: chord[0], key: chord[1] },
    ...(extra.chops ?? []).map((step) => ({ step, sound: chord[0], key: chord[1], volume: 24 })),
    ...b.bassNotes([1, 8, 12], bassKey),
    ...boom[groove](),
    ...(extra.lead ?? []).map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  const stabBar = (groove: keyof typeof boom, lead: [number, number, number?][] = []): Note[] => [
    ...b.bassNotes([1, 8, 12], bG),
    ...boom[groove](),
    ...[1, 4, 8, 11, 14].map((step, i) => ({ step, sound: 3, key: G7, volume: i % 2 ? 26 : 30 })),
    ...lead.map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  return {
    name: 'Dusty Crates',
    tempo: 88,
    swing: 10,
    melodic: {
      1: { id: 'min9', name: 'organ min9', samples: organChord([60, 63, 67, 70, 74], 0.85, 41) },
      2: { id: 'maj7', name: 'rhodes maj7', samples: rhodesChord([56, 60, 63, 67], 1.0, 42) },
      3: { id: 'dom7', name: 'brass dom7', samples: brassStab([55, 59, 62, 65], 0.35) },
      4: { id: 'bass', name: 'sub bass', samples: subBass(36, 0.5) },
      5: { id: 'lead', name: 'lead rhodes', samples: rhodesLead(67, 0.45, 43) },
    },
    // An 808 kick (kept shorter: the stab bars' kick, brass, bass and lead meet the hat on beat 3), 707 snare, rim and clap, 606 hats, 626 tambourine and cowbell.
    kits: {
      11: { kit: 'TR-808', trim: { [D.kick]: 0.15, [D.kick2]: 0.3 } },
      12: { kit: 'TR-707', trim: BOOM_TRIMS.snares },
      13: { kit: 'TR-606', trim: BOOM_TRIMS.hats },
      14: { kit: 'TR-626', trim: BOOM_TRIMS.perc },
    },
    colour: BOOM_COLOUR,
    bars: [
      bar(Cm, bC, 'main', { chops: [7] }),
      bar(Fm, bF, 'main', { chops: [7] }),
      bar(Ab, bAb, 'main', { chops: [7] }),
      stabBar('turn'),
      bar(Cm, bC, 'sparse', { lead: [[3, L.G], [7, L.Bb], [11, L.G, 26], [14, L.F, 24]] }),
      bar(Fm, bF, 'sparse', { lead: [[2, L.C], [6, L.Bb], [10, L.G, 26]] }),
      bar(Ab, bAb, 'sparse', { lead: [[3, L.Eb], [7, L.D], [11, L.C, 26], [14, L.Bb, 24]] }),
      stabBar('sparse', [[2, L.D], [6, L.Eb4, 26], [10, L.D4, 24]]),
    ],
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 1, 2, 3, 4],
  };
}

// House

const HOUSE_COLOUR: Record<number, Colour> = {
  1: { volume: 34, filter: 63 },
  2: { volume: 34, filter: 63 },
  3: { volume: 30, filter: 63 },
  4: { volume: 40, filter: 20 },
  5: { volume: 28, filter: 63 },
  11: { volume: 48, filter: 63 },
  12: { volume: 40, filter: 63 },
  13: { volume: 26, filter: 63 },
  14: { volume: 26, filter: 63 },
};

/** House drums on the standard kits: kick on 11, clap on 12, hats on 13 (closed, open, ride), percussion on 14. Four to the floor; the open hat on the "and". */
const house = {
  jack: (): Note[] => [
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 11, key: D.kick })),
    ...[5, 13].map((step) => ({ step, sound: 12, key: D.clap })),
    ...[3, 7, 11, 15].map((step) => ({ step, sound: 13, key: D.oh, volume: 26 })),
    ...[2, 4, 6, 8, 10, 12, 14, 16].map((step) => ({ step, sound: 13, key: D.ch, volume: 18 })),
  ],
  /** The jack without the closed hats, so the bleep hook has a voice. */
  jackSparse: (): Note[] => [
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 11, key: D.kick })),
    ...[5, 13].map((step) => ({ step, sound: 12, key: D.clap })),
    ...[3, 7, 11, 15].map((step) => ({ step, sound: 13, key: D.oh, volume: 26 })),
  ],
  /** No kick: the breakdown. */
  breakdown: (): Note[] => [
    ...[5, 13].map((step) => ({ step, sound: 12, key: D.clap })),
    ...[3, 7, 11, 15].map((step) => ({ step, sound: 13, key: D.oh, volume: 26 })),
    ...[2, 4, 6, 8, 10, 12, 14, 16].map((step) => ({ step, sound: 13, key: D.ch, volume: 18 })),
  ],
  /** Detroit: kick, clap, sixteenth hats on the offbeats, the hi conga (key 11) and clave (key 5) of the 808 percussion kit answering. */
  motor: (): Note[] => [
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 11, key: D.kick })),
    ...[5, 13].map((step) => ({ step, sound: 12, key: D.clap })),
    ...[2, 4, 6, 8, 10, 12, 14, 16].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 0 ? 22 : 16 })),
    { step: 4, sound: 14, key: 11, volume: 24 },
    { step: 12, sound: 14, key: 5, volume: 24 },
  ],
};

/** The house trims. */
const HOUSE_TRIMS = {
  kicks: { [D.kick]: 0.3, [D.kick2]: 0.3 },
  claps: { [D.clap]: 0.25, [D.snare]: 0.25 },
  hats: { [D.ch]: 0.1, [D.oh]: 0.28, [D.ride]: 0.3 },
};

export function warehouseJack(): SongSpec {
  // A minor, jacking: Am7 | Am7 | Fmaj | G (the major stab at F, +2 for G). Piano stabs; sawtooth bass at A1; bleep at A5.
  const Am: [number, number] = [1, K(0, 'Am7')];
  const F: [number, number] = [2, K(0, 'F')];
  const G: [number, number] = [2, K(2, 'G')];
  const bA = K(0, 'bass A');
  const bF = K(-4, 'bass F');
  const bG = K(-2, 'bass G');
  const bC = K(3, 'bass C');
  // Bleep at A5: E5 -5, G5 -2, A5 0, C6 +3, D6 +5.
  const L = { E: K(-5, 'E'), G: K(-2, 'G'), A: K(0, 'A'), C: K(3, 'C'), D: K(5, 'D') };
  /** Stabs on 1, 4, 7, 11 and 14, bass on the offbeat eighths. */
  const bar = (chord: [number, number], bassKey: number, groove: keyof typeof house, extra: { bassTurn?: number; lead?: [number, number, number?][] } = {}): Note[] => [
    ...[1, 4, 7, 11, 14].map((step, i) => ({ step, sound: chord[0], key: chord[1], volume: i ? 30 : 34 })),
    ...[3, 7, 11].map((step) => ({ step, sound: 4, key: bassKey })),
    { step: 15, sound: 4, key: extra.bassTurn ?? bassKey },
    ...house[groove](),
    ...(extra.lead ?? []).map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  return {
    name: 'Warehouse Jack',
    tempo: 122,
    swing: 2,
    melodic: {
      1: { id: 'min', name: 'piano stab min7', samples: pianoStab([57, 60, 64, 67], 0.35, 51) },
      2: { id: 'maj', name: 'piano stab maj', samples: pianoStab([53, 57, 60, 65], 0.35, 52) },
      4: { id: 'bass', name: 'bass', samples: houseBass(33, 0.25) },
      5: { id: 'lead', name: 'bleep', samples: bleep(81, 0.3) },
    },
    // All 909, with the 626's cowbell and tambourine for percussion.
    kits: {
      11: { kit: 'TR-909', trim: HOUSE_TRIMS.kicks },
      12: { kit: 'TR-909', trim: HOUSE_TRIMS.claps },
      13: { kit: 'TR-909', trim: HOUSE_TRIMS.hats },
      14: { kit: 'TR-626', trim: { 16: 0.2, 10: 0.2 } },
    },
    colour: HOUSE_COLOUR,
    bars: [
      bar(Am, bA, 'jack'),
      bar(Am, bA, 'jack', { bassTurn: bC }),
      bar(F, bF, 'jack'),
      bar(G, bG, 'jack', { bassTurn: bA }),
      bar(Am, bA, 'jackSparse', { lead: [[2, L.A], [6, L.C], [10, L.A, 24], [13, L.G, 24]] }),
      bar(Am, bA, 'jackSparse', { bassTurn: bC, lead: [[2, L.E], [6, L.G], [10, L.A, 24]] }),
      bar(F, bF, 'jackSparse', { lead: [[2, L.A], [6, L.C], [10, L.D, 24], [13, L.C, 24]] }),
      bar(G, bG, 'jackSparse', { bassTurn: bA, lead: [[2, L.D], [6, L.G, 24], [10, L.A, 24]] }),
      bar(Am, bA, 'breakdown'),
      bar(F, bF, 'breakdown', { bassTurn: bG }),
    ],
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 9, 10, 9, 10, 1, 2, 3, 4, 1, 2, 3, 4],
  };
}

export function motorCity(): SongSpec {
  // D minor: Dm9 | Gm9 | Bbmaj9 | Gm9 on string pads (min9 at D, Gm9 is +5; maj9 at Bb), a piano stab at D for accents; sawtooth bass at D1; bleep at D6.
  const Dm: [number, number] = [1, K(0, 'Dm9')];
  const Gm: [number, number] = [1, K(5, 'Gm9')];
  const Bb: [number, number] = [2, K(0, 'Bbmaj9')];
  const stab = K(0, 'stab');
  const bD = K(0, 'bass D');
  const bF = K(3, 'bass F');
  const bA = K(7, 'bass A');
  const bG = K(5, 'bass G');
  const bBb = K(8, 'bass Bb');
  // Bleep at D6: A5 -5, C6 -2, D6 0, F6 +3, G6 +5.
  const L = { A: K(-5, 'A'), C: K(-2, 'C'), D: K(0, 'D'), F: K(3, 'F'), G: K(5, 'G') };
  /** The pad on 1 and 9, a sixteenth bassline on the odd steps, the groove, stabs or the hook. */
  const bar = (chord: [number, number], bassline: number[], extra: { stabs?: number[]; lead?: [number, number, number?][] } = {}): Note[] => [
    { step: 1, sound: chord[0], key: chord[1] },
    { step: 9, sound: chord[0], key: chord[1], volume: 30 },
    ...[1, 3, 7, 9, 11, 15].map((step, i) => ({ step, sound: 4, key: bassline[i % bassline.length], volume: step % 4 === 1 ? 40 : 34 })),
    ...house.motor(),
    ...(extra.stabs ?? []).map((step) => ({ step, sound: 3, key: stab })),
    ...(extra.lead ?? []).map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  return {
    name: 'Motor City',
    tempo: 124,
    swing: 0,
    melodic: {
      1: { id: 'min9', name: 'strings min9', samples: stringPad([50, 53, 57, 60, 64], 0.7) },
      2: { id: 'maj9', name: 'strings maj9', samples: stringPad([46, 50, 53, 57, 60], 0.7) },
      3: { id: 'stab', name: 'piano stab', samples: pianoStab([62, 65, 69, 72], 0.3, 61) },
      4: { id: 'bass', name: 'bass', samples: houseBass(26, 0.2) },
      5: { id: 'lead', name: 'bleep', samples: bleep(86, 0.25) },
    },
    // A 909 kick and hats, the 808's clap, the 808 percussion kit's conga and clave.
    kits: {
      11: { kit: 'TR-909', trim: HOUSE_TRIMS.kicks },
      12: { kit: 'TR-808', trim: HOUSE_TRIMS.claps },
      13: { kit: 'TR-909', trim: HOUSE_TRIMS.hats },
      14: { kit: 'TR-808 Percussion', trim: { 11: 0.2, 5: 0.2 } },
    },
    colour: HOUSE_COLOUR,
    bars: [
      bar(Dm, [bD, bD, bF, bD, bA, bD]),
      bar(Gm, [bG, bG, bBb, bG, bD, bG]),
      bar(Bb, [bBb, bBb, bD, bBb, bF, bBb]),
      bar(Gm, [bG, bG, bBb, bG, bD, bA]),
      bar(Dm, [bD, bD, bF, bD, bA, bD], { lead: [[2, L.D], [6, L.F], [10, L.A, 24], [14, L.G, 24]] }),
      bar(Gm, [bG, bG, bBb, bG, bD, bG], { lead: [[2, L.G], [6, L.F], [10, L.D, 24]] }),
      bar(Bb, [bBb, bBb, bD, bBb, bF, bBb], { lead: [[2, L.D], [6, L.F], [10, L.G, 24], [14, L.F, 24]] }),
      bar(Gm, [bG, bG, bBb, bG, bD, bA], { stabs: [6, 10, 14] }),
    ],
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 1, 2, 3, 4],
  };
}

async function main(): Promise<void> {
  const [pack, out] = process.argv.slice(2);
  if (!pack || !out) throw new Error('usage: make-genre-packs.ts <TR pack folder> <output folder>');
  mkdirSync(out, { recursive: true });
  for (const spec of [cornerStore(), dustyCrates(), warehouseJack(), motorCity()]) console.log((await writePack(spec, pack, out)).description);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error((error as Error).message);
    process.exit(1);
  });
}
