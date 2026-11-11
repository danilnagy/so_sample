/**
 * Build the trap, jungle, dub and techno project packs (<name>.sosample.zip).
 *
 *   npx tsx scripts/make-more-packs.ts "<TR pack folder>" "<output folder>"
 *
 * Four songs that show the rest of what the device records: pitch locks that glide an
 * 808 bass (trap, 140 BPM, half time), filter and resonance locks sweeping a stab across
 * the bar (techno, 130 BPM), a fast break with a reese bass (jungle, 170 BPM) and a slow
 * one-drop with offbeat skanks and punch-in effects on the dub-out bars (dub, 75 BPM).
 * Same layout as the other packs: chords on 1 to 3, bass on 4, lead on 5, drums on 11 to
 * 14; every song is checked against the four voices and the 241 pages.
 */

import { mkdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

import { type Colour, D, type Note, type SongSpec, RATE, brassStab, finish, houseBass, lowpass, midiHz, mixInto, mustKey, organChord, saw, stringPad, subBass, writePack } from './pack-tools';

const K = (semitones: number, what: string): number => mustKey(semitones, what);

// Instruments of these packs

/** A bell: a sine with an inharmonic partial that dies first, for trap melodies. */
export function bell(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const hz = midiHz(midi);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const env = Math.min(1, t / 0.002);
    out[i] = env * (Math.exp(-t / 0.9) * Math.sin(2 * Math.PI * hz * t) + 0.35 * Math.exp(-t / 0.25) * Math.sin(2 * Math.PI * hz * 2.76 * t) + 0.15 * Math.exp(-t / 0.5) * Math.sin(2 * Math.PI * hz * 2 * t));
  }
  return finish(out, 0.8);
}

/** A reese bass: two detuned sawtooths beating slowly under a low-pass, long. */
export function reeseBass(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const mix = new Float64Array(n);
  mixInto(mix, saw(midiHz(midi), n, -0.004), 0.5);
  mixInto(mix, saw(midiHz(midi), n, 0.004), 0.5);
  const soft = lowpass(lowpass(mix, 900), 900);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    soft[i] *= Math.min(1, t / 0.01) * Math.exp(-t / 1.2);
  }
  return finish(soft, 0.9, 0.04);
}

/** A melodica: a bright square-ish reed with a slow vibrato, for dub lines. */
export function melodica(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const hz = midiHz(midi);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const vibrato = 1 + 0.004 * Math.sin(2 * Math.PI * 5.5 * t) * Math.min(1, t / 0.3);
    const phase = 2 * Math.PI * hz * vibrato * t;
    let v = 0;
    for (const h of [1, 3, 5, 7]) v += Math.sin(h * phase) / h;
    out[i] = v * Math.min(1, t / 0.02) * Math.exp(-t / 1.6);
  }
  return finish(lowpass(out, 3200), 0.8, 0.05);
}

/** A techno stab: a sawtooth chord with a touch of detune, short, so the step locks shape it. */
export function technoStab(midis: number[], seconds: number): Float64Array {
  return brassStab(midis, seconds);
}

/** A dark pad: the string pad under a lower filter, for trap. */
export function darkPad(midis: number[], seconds: number): Float64Array {
  return finish(lowpass(stringPad(midis, seconds), 1400), 0.8, 0.08);
}

// Trap

const TRAP_COLOUR: Record<number, Colour> = {
  1: { volume: 30, filter: 63 },
  2: { volume: 28, filter: 63 },
  3: { volume: 30, filter: 63 },
  4: { volume: 46, filter: 63 },
  11: { volume: 48, filter: 63 },
  12: { volume: 44, filter: 63 },
  13: { volume: 26, filter: 63 },
  14: { volume: 30, filter: 63 },
};

/**
 * Trap drums: half time, the snare on 3. The pad and the 808 hold two of the four voices
 * for most of the bar, so the hats take the offbeat eighths, skipping the kick and snare
 * steps, and roll into the bar's end: a sixteenth, then retriggered twice and three times.
 */
const trap = {
  main: (): Note[] => [
    { step: 1, sound: 11, key: D.kick },
    { step: 8, sound: 11, key: D.kick, volume: 42 },
    { step: 9, sound: 12, key: D.snare },
    ...[3, 5, 7, 11, 13].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 1 ? 26 : 20 })),
    // The roll into the next bar, as trap hats roll: a sixteenth, then the hat retriggered twice and three times (a triplet) within its step.
    { step: 14, sound: 13, key: D.ch, volume: 22 },
    { step: 15, sound: 13, key: D.ch, volume: 26, timing: 2 },
    { step: 16, sound: 13, key: D.ch, volume: 30, timing: 3 },
  ],
  /** The variation: the clap takes the snare's place, a kick lands on the "and" of 3, an open hat on the "and" of 4. */
  turn: (): Note[] => [
    { step: 1, sound: 11, key: D.kick },
    { step: 8, sound: 11, key: D.kick, volume: 42 },
    { step: 11, sound: 11, key: D.kick, volume: 40 },
    { step: 9, sound: 12, key: D.clap },
    ...[3, 5, 7, 13].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 1 ? 26 : 20 })),
    { step: 15, sound: 13, key: D.oh, volume: 24 },
  ],
  /** The intro: hats and snare alone. */
  sparse: (): Note[] => [{ step: 9, sound: 12, key: D.snare, volume: 38 }, ...[1, 3, 5, 7, 9, 11, 13, 15].map((step) => ({ step, sound: 13, key: D.ch, volume: 20 }))],
};

export function lateShift(): SongSpec {
  // F minor: Fm | Db | Ab | Eb. A minor pad at F and a major pad at Db (Ab is +7, Eb is +2); the bell at F5; the 808 is the pack's long 808, played across the keys.
  const Fm: [number, number] = [1, K(0, 'Fm')];
  const Db: [number, number] = [2, K(0, 'Db')];
  const Ab: [number, number] = [2, K(7, 'Ab')];
  const Eb: [number, number] = [2, K(2, 'Eb')];
  const bF = K(0, 'bass F');
  const bDb = K(-4, 'bass Db');
  const bAb = K(3, 'bass Ab');
  const bEb = K(-2, 'bass Eb');
  // Bell at F5: C5 -5, Eb5 -2, F5 0, Ab5 +3, Bb5 +5, C6 +7.
  const L = { C: K(-5, 'C'), Eb: K(-2, 'Eb'), F: K(0, 'F'), Ab: K(3, 'Ab'), Bb: K(5, 'Bb'), C6: K(7, 'C6') };
  /** The pad on 1; the 808 on 1 and on the "and" of 3 (step 7), where it glides a whole step up through the pitch lock; the groove; the bell line. */
  const bar = (chord: [number, number], bassKey: number, groove: keyof typeof trap, extra: { glide?: boolean; lead?: [number, number, number?][] } = {}): Note[] => [
    { step: 1, sound: chord[0], key: chord[1] },
    { step: 1, sound: 4, key: bassKey },
    { step: 7, sound: 4, key: bassKey, volume: 42, pitch: extra.glide ? 15 : 13 },
    { step: 12, sound: 4, key: bassKey, volume: 40 },
    ...trap[groove](),
    ...(extra.lead ?? []).map(([step, key, volume]) => ({ step, sound: 2, key, volume })),
  ];
  return {
    name: 'Late Shift',
    tempo: 140,
    swing: 0,
    melodic: {
      1: { id: 'min', name: 'pad minor', samples: darkPad([53, 56, 60, 65], 1.5) },
      2: { id: 'bell', name: 'bell', samples: bell(77, 0.35) },
      3: { id: 'maj', name: 'pad major', samples: darkPad([49, 53, 56, 61], 1.5) },
      4: { id: '808', name: '808 bass', hit: ['ROLAND TR-808 (1980)/[BD] Bass Drum (808s)/TR-808 BD Long 808s 02', 0.45] },
    },
    // All 808: the kick kept very short so the pad and the 808 bass have their voices.
    kits: {
      11: { kit: 'TR-808', trim: { [D.kick]: 0.15 } },
      12: { kit: 'TR-808', trim: { [D.snare]: 0.25, [D.clap]: 0.25 } },
      13: { kit: 'TR-808', trim: { [D.ch]: 0.08, [D.oh]: 0.3 } },
      14: { kit: 'TR-808', trim: { [D.rim]: 0.12, [D.lt]: 0.3 } },
    },
    colour: TRAP_COLOUR,
    bars: [
      bar(Fm, bF, 'main'),
      bar([3, Db[1]], bDb, 'main', { glide: true }),
      bar([3, Ab[1]], bAb, 'main'),
      bar([3, Eb[1]], bEb, 'turn', { glide: true }),
      // The bells fall on steps the kick and snare leave free: 3, 6, 10 and 13.
      bar(Fm, bF, 'main', { lead: [[3, L.F], [6, L.Ab], [10, L.F, 26], [13, L.Eb, 24]] }),
      bar([3, Db[1]], bDb, 'main', { glide: true, lead: [[3, L.Ab], [6, L.F, 26], [10, L.Eb, 24]] }),
      bar([3, Ab[1]], bAb, 'main', { lead: [[3, L.C6], [6, L.Bb], [10, L.Ab, 26], [13, L.F, 24]] }),
      bar([3, Eb[1]], bEb, 'turn', { glide: true, lead: [[3, L.F], [6, L.Eb, 26], [10, L.C, 24]] }),
      bar(Fm, bF, 'sparse'),
      bar([3, Db[1]], bDb, 'sparse', { glide: true }),
    ],
    chain: [9, 10, 9, 10, 1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 1, 2, 3, 4],
  };
}

// Jungle

const JUNGLE_COLOUR: Record<number, Colour> = {
  1: { volume: 30, filter: 63 },
  3: { volume: 30, filter: 63 },
  4: { volume: 44, filter: 18 },
  5: { volume: 28, filter: 63 },
  11: { volume: 48, filter: 63 },
  12: { volume: 44, filter: 63 },
  13: { volume: 24, filter: 63 },
  14: { volume: 30, filter: 63 },
};

/** Jungle drums at 170: a two-step break (kick 1 and 11, snare 5 and 13), ghost rims, eighth hats with the open hat on 15, a crash on the drop. */
const jungle = {
  main: (): Note[] => [
    { step: 1, sound: 11, key: D.kick },
    { step: 11, sound: 11, key: D.kick },
    { step: 5, sound: 12, key: D.snare },
    { step: 13, sound: 12, key: D.snare },
    { step: 8, sound: 12, key: D.rim, volume: 28 },
    { step: 16, sound: 12, key: D.rim, volume: 26 },
    ...[1, 3, 5, 7, 9, 11, 13].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 1 ? 24 : 18 })),
    { step: 15, sound: 13, key: D.oh, volume: 24 },
  ],
  /** The switch: the kick doubles on 3, the snare moves to 12, a tom fill at the end. */
  fill: (): Note[] => [
    { step: 1, sound: 11, key: D.kick },
    { step: 3, sound: 11, key: D.kick, volume: 40 },
    { step: 11, sound: 11, key: D.kick },
    { step: 5, sound: 12, key: D.snare },
    // The moved snare dragged: two hits within its step, as a jungle snare rolls into a fill.
    { step: 12, sound: 12, key: D.snare, timing: 2 },
    { step: 14, sound: 14, key: D.ht, volume: 34 },
    { step: 15, sound: 14, key: D.ht, volume: 38 },
    { step: 16, sound: 14, key: D.crash, volume: 40 },
    ...[1, 3, 5, 7, 9].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 1 ? 24 : 18 })),
  ],
  /** The drop: the crash on 1 over the main break. */
  drop: (): Note[] => [{ step: 1, sound: 14, key: D.crash, volume: 36 }, ...jungle.main().filter((n) => !(n.sound === 13 && n.step === 1))],
};

export function rinseOut(): SongSpec {
  // G minor: Gm | Gm | Eb | F stabs (an organ minor at G; the Eb and F from a major voicing at Eb, F being +2); the reese at G1, sweeping its filter up through the eight bars.
  const Gm: [number, number] = [1, K(0, 'Gm')];
  const Eb: [number, number] = [3, K(0, 'Eb')];
  const F: [number, number] = [3, K(2, 'F')];
  const bG = K(0, 'bass G');
  const bF = K(-2, 'bass F');
  const bEb = K(-4, 'bass Eb');
  const bBb = K(3, 'bass Bb');
  // Bleep hook at G5: D5 -5, F5 -2, G5 0, Bb5 +3, C6 +5.
  const L = { D: K(-5, 'D'), F: K(-2, 'F'), G: K(0, 'G'), Bb: K(3, 'Bb'), C: K(5, 'C') };
  /** The reese on 1 and 9 with the bar's filter lock, stabs on 3 and 10, the break, the hook. */
  const bar = (chord: [number, number], bass: [number, number], filter: number, groove: keyof typeof jungle, lead: [number, number, number?][] = []): Note[] => [
    { step: 1, sound: 4, key: bass[0], filter },
    { step: 9, sound: 4, key: bass[1], filter: Math.min(26, filter + 2), volume: 40 },
    { step: 3, sound: chord[0], key: chord[1] },
    { step: 10, sound: chord[0], key: chord[1], volume: 26 },
    ...jungle[groove](),
    ...lead.map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  return {
    name: 'Rinse Out',
    tempo: 170,
    swing: 0,
    melodic: {
      1: { id: 'min', name: 'organ minor', samples: organChord([55, 58, 62, 67], 0.4, 71) },
      3: { id: 'maj', name: 'organ major', samples: organChord([51, 55, 58, 63], 0.4, 72) },
      // Short enough that the lower keys, which play it slower, still end before the next bass note.
      4: { id: 'reese', name: 'reese bass', samples: reeseBass(31, 0.55) },
      5: { id: 'hook', name: 'hook', samples: bell(79, 0.25) },
    },
    // 909 kicks, snare and rim, 606 hats, the 909's high tom and crash; everything short for the break.
    kits: {
      11: { kit: 'TR-909', trim: { [D.kick]: 0.15, [D.kick2]: 0.15 } },
      12: { kit: 'TR-909', trim: { [D.snare]: 0.2, [D.rim]: 0.1 } },
      13: { kit: 'TR-606', trim: { [D.ch]: 0.08, [D.oh]: 0.2 } },
      14: { kit: 'TR-909', trim: { [D.ht]: 0.15, [D.crash]: 0.2 } },
    },
    colour: JUNGLE_COLOUR,
    bars: [
      // The filter opens over the first four bars (12, 16, 20, 24) and sits open through the drop.
      bar(Gm, [bG, bG], 12, 'main'),
      bar(Gm, [bG, bBb], 16, 'main'),
      bar(Eb, [bEb, bEb], 20, 'main'),
      bar(F, [bF, bG], 24, 'fill'),
      bar(Gm, [bG, bG], 26, 'drop', [[2, L.G], [6, L.Bb], [8, L.G, 24], [14, L.F, 24]]),
      bar(Gm, [bG, bBb], 26, 'main', [[2, L.D], [6, L.F, 24], [14, L.G, 24]]),
      bar(Eb, [bEb, bEb], 26, 'main', [[2, L.Bb], [6, L.C], [8, L.Bb, 24], [14, L.G, 24]]),
      bar(F, [bF, bG], 26, 'fill', [[6, L.F], [12, L.D, 24]]),
    ],
    chain: [1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 1, 2, 3, 4, 5, 6, 7, 8],
  };
}

// Dub

const DUB_COLOUR: Record<number, Colour> = {
  1: { volume: 28, filter: 30 },
  2: { volume: 28, filter: 30 },
  4: { volume: 46, filter: 14 },
  5: { volume: 30, filter: 26 },
  11: { volume: 46, filter: 63 },
  12: { volume: 40, filter: 63 },
  13: { volume: 22, filter: 40 },
  14: { volume: 28, filter: 40 },
};

/** The one drop: kick and rim together on 3 (step 9), eighth hats with the open hat on 15, a shaker on the offbeats. */
const dub = {
  oneDrop: (): Note[] => [
    { step: 9, sound: 11, key: D.kick },
    { step: 9, sound: 12, key: D.rim },
    ...[1, 3, 5, 7, 11, 13].map((step) => ({ step, sound: 13, key: D.ch, volume: step % 4 === 1 ? 24 : 18 })),
    { step: 15, sound: 13, key: D.oh, volume: 24 },
    ...[4, 8, 12].map((step) => ({ step, sound: 14, key: D.ch2, volume: 20 })),
  ],
  /** The dub-out: drums thin to the kick and the rim, the snare answers late. */
  dubOut: (): Note[] => [
    { step: 9, sound: 11, key: D.kick },
    { step: 9, sound: 12, key: D.rim },
    { step: 16, sound: 12, key: D.snare, volume: 36 },
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 13, key: D.ch, volume: 20 })),
  ],
};

export function echoChamber(): SongSpec {
  // A minor: Am | Am | Dm | E. Skanks from a minor organ at A (Dm is +5) and a major at E; the sub walks A, C, D, E; the melodica at A4.
  const Am: [number, number] = [1, K(0, 'Am')];
  const Dm: [number, number] = [1, K(5, 'Dm')];
  const E: [number, number] = [2, K(0, 'E')];
  const bA = K(0, 'bass A');
  const bC = K(3, 'bass C');
  const bD = K(5, 'bass D');
  const bE = K(7, 'bass E');
  const bG = K(-2, 'bass G');
  // Melodica at A4: E4 -5, G4 -2, A4 0, B4 +2, C5 +3, D5 +5, E5 +7.
  const L = { E4: K(-5, 'E4'), G: K(-2, 'G'), A: K(0, 'A'), B: K(2, 'B'), C: K(3, 'C'), D: K(5, 'D'), E: K(7, 'E') };
  /** Skanks on the offbeats (3, 7, 11, 15), the bass on 1 and 7 with a pickup on 15, the drums, the melodica. */
  const bar = (chord: [number, number], bass: [number, number, number?], groove: keyof typeof dub, lead: [number, number, number?][] = []): Note[] => [
    ...[3, 7, 11, 15].map((step, i) => ({ step, sound: chord[0], key: chord[1], volume: i % 2 ? 26 : 28 })),
    { step: 1, sound: 4, key: bass[0] },
    { step: 7, sound: 4, key: bass[1], volume: 42 },
    ...(bass[2] !== undefined ? [{ step: 16, sound: 4, key: bass[2], volume: 38 }] : []),
    ...dub[groove](),
    ...lead.map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  const none: (number | null)[] = new Array(16).fill(null);
  /** The dub-out bars: the retrigger effect (12) echoes the held skank across the last beat, and the reverse (15) turns the pickup round. */
  const echo = none.map((_, i) => (i >= 12 && i <= 14 ? 12 : i === 15 ? 15 : null));
  return {
    name: 'Echo Chamber',
    tempo: 75,
    swing: 4,
    melodic: {
      1: { id: 'min', name: 'skank minor', samples: organChord([57, 60, 64, 69], 0.25, 81) },
      2: { id: 'maj', name: 'skank major', samples: organChord([56, 59, 64, 68], 0.25, 82) },
      4: { id: 'sub', name: 'sub bass', samples: subBass(33, 0.5) },
      5: { id: 'melodica', name: 'melodica', samples: melodica(69, 0.6) },
    },
    // 808 kick, rim, snare and hats; the 626's shaker (key 8) for the offbeats.
    kits: {
      11: { kit: 'TR-808', trim: { [D.kick]: 0.3 } },
      12: { kit: 'TR-808', trim: { [D.rim]: 0.15, [D.snare]: 0.3 } },
      13: { kit: 'TR-808', trim: { [D.ch]: 0.1, [D.oh]: 0.4 } },
      14: { kit: 'TR-626', trim: { [D.ch2]: 0.12, [D.perc]: 0.2 } },
    },
    colour: DUB_COLOUR,
    bars: [
      bar(Am, [bA, bA, bG], 'oneDrop'),
      bar(Am, [bA, bC], 'oneDrop'),
      bar(Dm, [bD, bD, bC], 'oneDrop'),
      bar(E, [bE, bE, bG], 'oneDrop'),
      // The melodica enters on the "and" of 1 (step 2), after the bar's sub and hat have taken their voices.
      bar(Am, [bA, bA, bG], 'oneDrop', [[2, L.E], [6, L.C], [10, L.A, 28], [13, L.G, 26]]),
      bar(Am, [bA, bC], 'oneDrop', [[6, L.B], [10, L.C, 28], [13, L.A, 26]]),
      bar(Dm, [bD, bD, bC], 'oneDrop', [[2, L.D], [6, L.E], [10, L.D, 28], [13, L.C, 26]]),
      bar(E, [bE, bE, bG], 'oneDrop', [[6, L.B], [10, L.E4, 28], [13, L.G, 26]]),
      bar(Am, [bA, bA], 'dubOut'),
      bar(E, [bE, bE], 'dubOut'),
    ],
    effects: { 8: echo, 9: echo },
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 9, 10, 9, 10, 1, 2, 3, 4],
  };
}

// Techno

const TECHNO_COLOUR: Record<number, Colour> = {
  1: { volume: 32, filter: 12, resonance: 32 },
  4: { volume: 40, filter: 22 },
  5: { volume: 26, filter: 63 },
  11: { volume: 50, filter: 63 },
  12: { volume: 40, filter: 63 },
  13: { volume: 24, filter: 63 },
  14: { volume: 26, filter: 63 },
};

/** Techno drums at 130: four kicks, the clap on 2 and 4, offbeat closed hats, the open hat on the "and" of 4, a rim answering. */
const techno = {
  drive: (): Note[] => [
    ...[1, 5, 9, 13].map((step) => ({ step, sound: 11, key: D.kick })),
    ...[5, 13].map((step) => ({ step, sound: 12, key: D.clap })),
    ...[3, 7, 11].map((step) => ({ step, sound: 13, key: D.ch, volume: 22 })),
    { step: 15, sound: 13, key: D.oh, volume: 26 },
    { step: 12, sound: 14, key: D.rim, volume: 24 },
  ],
  /** The break: no kick; the ride keeps time. */
  breakdown: (): Note[] => [...[5, 13].map((step) => ({ step, sound: 12, key: D.clap })), ...[1, 5, 9, 13].map((step) => ({ step, sound: 13, key: D.ride, volume: 22 })), { step: 15, sound: 13, key: D.oh, volume: 26 }],
};

export function concrete(): SongSpec {
  // A minor, one stab (Am at 0, with G at -2 and F at -4 for the turn), its filter rising across each bar as a lock on every hit and its resonance set high; the bass rolls on the offbeat sixteenths at A1; the bleep at A5.
  const stab = K(0, 'stab A');
  const stabG = K(-2, 'stab G');
  const stabF = K(-4, 'stab F');
  const bA = K(0, 'bass A');
  const bG = K(-2, 'bass G');
  const bF = K(-4, 'bass F');
  const bC = K(3, 'bass C');
  // Bleep at A5: E5 -5, G5 -2, A5 0, C6 +3, D6 +5.
  const L = { E: K(-5, 'E'), G: K(-2, 'G'), A: K(0, 'A'), C: K(3, 'C'), D: K(5, 'D') };
  /** Stabs on 1, 4, 7, 10 and 14 with the filter climbing (a sweep across the bar); the bass on the even steps; the drums; the hook. */
  const bar = (stabKey: number, bassKey: number, sweep: [number, number], groove: keyof typeof techno, extra: { turn?: number; lead?: [number, number, number?][] } = {}): Note[] => [
    ...[1, 4, 7, 10, 14].map((step, i, all) => ({ step, sound: 1, key: stabKey, filter: Math.round(sweep[0] + ((sweep[1] - sweep[0]) * i) / (all.length - 1)) })),
    ...[2, 4, 6, 8, 10, 12, 14].map((step) => ({ step, sound: 4, key: bassKey, volume: step % 4 === 0 ? 40 : 34 })),
    { step: 16, sound: 4, key: extra.turn ?? bassKey, volume: 38 },
    ...techno[groove](),
    ...(extra.lead ?? []).map(([step, key, volume]) => ({ step, sound: 5, key, volume })),
  ];
  return {
    name: 'Concrete',
    tempo: 130,
    swing: 0,
    melodic: {
      1: { id: 'stab', name: 'stab minor', samples: technoStab([57, 60, 64, 69], 0.28) },
      4: { id: 'bass', name: 'bass', samples: houseBass(33, 0.15) },
      5: { id: 'bleep', name: 'bleep', samples: bell(81, 0.3) },
    },
    // All 909, short.
    kits: {
      11: { kit: 'TR-909', trim: { [D.kick]: 0.15 } },
      12: { kit: 'TR-909', trim: { [D.clap]: 0.22, [D.snare]: 0.22 } },
      13: { kit: 'TR-909', trim: { [D.ch]: 0.08, [D.oh]: 0.18, [D.ride]: 0.25 } },
      14: { kit: 'TR-909', trim: { [D.rim]: 0.1, [D.mt]: 0.25 } },
    },
    colour: TECHNO_COLOUR,
    bars: [
      // Each bar sweeps the stab's filter a little higher than the last: 8..14, 10..16, 12..20, 14..24.
      bar(stab, bA, [8, 14], 'drive'),
      bar(stab, bA, [10, 16], 'drive', { turn: bC }),
      bar(stab, bA, [12, 20], 'drive'),
      bar(stabG, bG, [14, 24], 'drive', { turn: bF }),
      // The hook keeps to steps 2 and 10, where the kick and clap leave a voice.
      bar(stab, bA, [16, 26], 'drive', { lead: [[2, L.A], [10, L.C, 24]] }),
      bar(stab, bA, [16, 26], 'drive', { turn: bC, lead: [[2, L.E], [10, L.G, 24]] }),
      bar(stabF, bF, [16, 26], 'drive', { lead: [[2, L.A], [10, L.D, 24]] }),
      bar(stabG, bG, [16, 26], 'drive', { turn: bA, lead: [[2, L.D], [10, L.A, 24]] }),
      // The breakdown closes the filter again.
      bar(stab, bA, [14, 8], 'breakdown'),
      bar(stabG, bG, [12, 6], 'breakdown', { turn: bA }),
    ],
    chain: [1, 2, 3, 4, 1, 2, 3, 4, 5, 6, 7, 8, 5, 6, 7, 8, 9, 10, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8],
  };
}

async function main(): Promise<void> {
  const [pack, out] = process.argv.slice(2);
  if (!pack || !out) throw new Error('usage: make-more-packs.ts <TR pack folder> <output folder>');
  mkdirSync(out, { recursive: true });
  for (const spec of [lateShift(), rinseOut(), echoChamber(), concrete()]) console.log((await writePack(spec, pack, out)).description);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error((error as Error).message);
    process.exit(1);
  });
}
