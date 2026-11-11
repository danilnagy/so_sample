/**
 * Afterglow: italo disco at 118 BPM, the bundled project that shows melodic note lengths
 * (docs/aux-nibble-results.md). Its instruments sustain, so a note's length, not its
 * sample's decay, sets the rhythm:
 *
 * - a string pad, gated: the chords hit on a syncopated pattern, each cut to one or two
 *   steps, as an italo or trance gate chops a held chord; in the intro and breakdown the same
 *   pad plays at full length, for contrast;
 * - a saw bass in octaves: eighth notes jumping between the root and the octave below, each
 *   cut to one step, the genre's bounce;
 * - a square lead arpeggio: staccato one-step notes, with a held note ending each phrase.
 *
 * A minor, Am | F | C | G. Standard kits: the 707's kick and hats, the 808's clap.
 */

import { type Colour, D, type Note, type SongSpec, RATE, finish, lowpass, midiHz, mustKey, saw, stringPad } from './pack-tools';

const K = (semitones: number, what: string): number => mustKey(semitones, what);

// Instruments of this pack: both sustain, so their notes' lengths shape them.

/** A saw bass that holds: one sawtooth and its octave, under a low-pass, decaying slowly. */
export function synthBass(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const mix = new Float64Array(n);
  const low = saw(midiHz(midi), n);
  const sub = saw(midiHz(midi) / 2, n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    mix[i] = (low[i] * 0.7 + sub[i] * 0.3) * Math.min(1, t / 0.004) * Math.exp(-t / 2);
  }
  return finish(lowpass(lowpass(mix, 900), 1800), 0.9, 0.02);
}

/** A square lead that holds: odd harmonics, a slight vibrato fading in, a soft low-pass. */
export function synthLead(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const hz = midiHz(midi);
  const out = new Float64Array(n);
  let phase = 0;
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    phase += (2 * Math.PI * hz * (1 + 0.003 * Math.sin(2 * Math.PI * 5 * t) * Math.min(1, t / 0.4))) / RATE;
    let v = 0;
    for (const h of [1, 3, 5, 7, 9]) v += Math.sin(h * phase) / h;
    out[i] = v * Math.min(1, t / 0.005) * Math.exp(-t / 3);
  }
  return finish(lowpass(out, 3000), 0.8, 0.02);
}

const ITALO_COLOUR: Record<number, Colour> = {
  1: { volume: 30, filter: 63 },
  2: { volume: 30, filter: 63 },
  4: { volume: 42, filter: 26 },
  5: { volume: 28, filter: 63 },
  11: { volume: 48, filter: 63 },
  12: { volume: 40, filter: 63 },
  13: { volume: 24, filter: 63 },
};

/** Italo drums: four to the floor, the clap on 2 and 4, the open hat on every "and". */
const drums = (): Note[] => [
  ...[1, 5, 9, 13].map((step) => ({ step, sound: 11, key: D.kick })),
  ...[5, 13].map((step) => ({ step, sound: 12, key: D.clap })),
  ...[3, 7, 11, 15].map((step) => ({ step, sound: 13, key: D.oh })),
];

export function afterglow(): SongSpec {
  // Pads: a minor chord at A (sound 1), a major chord at F (sound 2), C is +7 and G is +2 from it.
  const Am: [number, number] = [1, K(0, 'Am')];
  const F: [number, number] = [2, K(0, 'F')];
  const C: [number, number] = [2, K(7, 'C')];
  const G: [number, number] = [2, K(2, 'G')];
  // The bass sample is G2: every root and the octave below it lie on the keys.
  const bass = { Am: [K(2, 'A'), K(-10, 'A low')], F: [K(10, 'F'), K(-2, 'F low')], C: [K(5, 'C'), K(-7, 'C low')], G: [K(0, 'G'), K(-12, 'G low')] } as const;
  // The lead sample is A4: the chord tones of each chord.
  const arp = { Am: [K(0, 'A4'), K(3, 'C5'), K(7, 'E5')], F: [K(-4, 'F4'), K(0, 'A4'), K(3, 'C5')], C: [K(3, 'C5'), K(7, 'E5'), K(10, 'G5')], G: [K(-2, 'G4'), K(2, 'B4'), K(5, 'D5')] } as const;
  type Chord = keyof typeof arp;
  const pads: Record<Chord, [number, number]> = { Am, F, C, G };

  /** The octave bass: eighths, low then high, each cut to one step. */
  const bassLine = (chord: Chord): Note[] =>
    [1, 3, 5, 7, 9, 11, 13, 15].map((step, i) => ({ step, sound: 4, key: bass[chord][i % 2 ? 0 : 1], timing: 1 }));
  /** The gate: the chord on a syncopated three-three-two, cut to two steps, one step, two, one, two. */
  const gate = (chord: Chord): Note[] =>
    (
      [
        [1, 2],
        [4, 1],
        [7, 2],
        [11, 1],
        [13, 2],
      ] as const
    ).map(([step, length]) => ({ step, sound: pads[chord][0], key: pads[chord][1], timing: length }));
  /** The arpeggio between the beats: staccato one-step notes up the chord, the phrase's last note held for three steps. */
  const arpeggio = (chord: Chord, last: boolean): Note[] => [
    ...[2, 4, 6, 8, 10, 12].map((step, i) => ({ step, sound: 5, key: arp[chord][i % 3], timing: 1 })),
    { step: 14, sound: 5, key: arp[chord][last ? 2 : 1], timing: 3, volume: 30 },
  ];
  /** The pad held at full length: the default, no length at all. */
  const held = (chord: Chord): Note[] => [{ step: 1, sound: pads[chord][0], key: pads[chord][1] }];

  const order: Chord[] = ['Am', 'F', 'C', 'G'];
  return {
    name: 'Afterglow',
    tempo: 118,
    swing: 0,
    melodic: {
      1: { id: 'pad-min', name: 'pad minor', samples: stringPad([57, 60, 64], 1.8) },
      2: { id: 'pad-maj', name: 'pad major', samples: stringPad([53, 57, 60], 1.8) },
      4: { id: 'bass', name: 'saw bass', samples: synthBass(43, 1.0) },
      5: { id: 'lead', name: 'square lead', samples: synthLead(69, 1.2) },
    },
    kits: {
      11: { kit: 'TR-707', trim: { [D.kick]: 0.15 } },
      12: { kit: 'TR-808', trim: { [D.clap]: 0.2 } },
      13: { kit: 'TR-707', trim: { [D.oh]: 0.1 } },
    },
    colour: ITALO_COLOUR,
    bars: [
      // Patterns 1-4, the intro: the pad held, the arpeggio over it, no drums.
      ...order.map((c, i) => [...held(c), ...arpeggio(c, i === 3)]),
      // Patterns 5-8, the groove: drums, the octave bass and the gated pad.
      ...order.map((c) => [...drums(), ...bassLine(c), ...gate(c)]),
      // Patterns 9-12, the hook: drums, the bass and the arpeggio, the pad gated on the downbeat alone.
      ...order.map((c, i) => [...drums(), ...bassLine(c), ...arpeggio(c, i === 3), { step: 1, sound: pads[c][0], key: pads[c][1], timing: 2 }]),
      // Patterns 13-16, the breakdown: the pad held and the bass in long notes, no drums.
      ...order.map((c) => [...held(c), { step: 1, sound: 4, key: bass[c][1], timing: 8 }, { step: 9, sound: 4, key: bass[c][0], timing: 6 }]),
    ],
    chain: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 5, 6, 7, 8, 9, 10, 11, 12],
  };
}
