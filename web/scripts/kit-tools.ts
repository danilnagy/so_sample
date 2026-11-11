/**
 * The standard drum kits, one per TR machine, in two forms: synthesized (drum-synth.ts),
 * freely licensed and the ones the app ships, or built from the TR pack's samples when a
 * pack folder is given, for local use only (that audio may not be redistributed).
 *
 * The standard drum kits, one per TR machine, shared by the kit archives (make-kits.ts)
 * and the bundled projects (pack-tools.ts), so a hit a kit and a project both use is one
 * library sample, byte for byte, with the same edit.
 *
 * Every kit uses the same key layout, so a pattern written for one kit plays sensibly on
 * another: 1 kick, 2 kick 2, 3 snare, 4 snare 2, 5 rimshot, 6 clap, 7 closed hat,
 * 8 closed hat 2, 9 open hat, 10 open hat 2, 11 crash, 12 ride, 13 low tom, 14 mid tom,
 * 15 high tom, 16 percussion. Keys a machine cannot fill stay empty. Long tails are cut
 * at each key's cap with a short fade, so the samples stay small: ten projects and seven
 * kits ship inside the app, and every hit is one library sample shared by all of them.
 */

import { readFileSync } from 'node:fs';
import { basename, join } from 'node:path';

import type { ArchiveSample } from '../src/core/archive';
import { SAMPLE_RATE, encodeMulaw } from '../src/core/mulaw';
import type { Clip } from '../src/core/project';
import { toNativeRate } from '../src/core/resample';
import { parseWav } from '../src/core/wav';
import { machineOf, synthHit, trimmedLength } from './drum-synth';

/** The standard keys, by role. */
export const D = { kick: 1, kick2: 2, snare: 3, snare2: 4, rim: 5, clap: 6, ch: 7, ch2: 8, oh: 9, oh2: 10, crash: 11, ride: 12, lt: 13, mt: 14, ht: 15, perc: 16 } as const;

/**
 * Longest a key plays, in seconds, by key. The device holds 241 pages of 4096 codes for
 * all sixteen sounds, so a kit is kept near 30 pages: kicks keep their body, hats and
 * rimshots are short, cymbals get the most.
 */
export const CAP_SECONDS: Record<number, number> = { 1: 0.5, 2: 0.6, 3: 0.3, 4: 0.3, 5: 0.15, 6: 0.3, 7: 0.15, 8: 0.15, 9: 0.5, 10: 0.5, 11: 0.9, 12: 0.7, 13: 0.35, 14: 0.3, 15: 0.3, 16: 0.25 };
const DEFAULT_CAP_SECONDS = 0.3;
const FADE_SECONDS = 0.04;

export interface KitSpec {
  name: string;
  /** Library folder the samples land in: the machine. */
  folder: string;
  /** Machine folder inside the pack. */
  machine: string;
  /** Key 1..16 to "category folder/file name" (no extension). */
  keys: Record<number, string>;
}

export const KITS: KitSpec[] = [
  {
    name: 'TR-505',
    folder: 'TR-505',
    machine: 'ROLAND TR-505 (1986)',
    keys: { 1: 'Kick/TR-505 Kick', 3: 'Snare/TR-505 Snare', 5: 'Percs/TR-505 Rim', 6: 'Clap/TR-505 Clap', 7: 'Hi Hat/TR-505 HiHat', 9: 'Cymbals/TR-505 Open Hat', 11: 'Cymbals/TR-505 Crash', 12: 'Cymbals/TR-505 Ride', 13: 'Tom/TR-505 Tom 3', 14: 'Tom/TR-505 Tom 2', 15: 'Tom/TR-505 Tom 1', 16: 'Percs/TR-505 Conga Hi' },
  },
  {
    name: 'TR-606',
    folder: 'TR-606',
    machine: 'ROLAND TR-606 Drumatix (1981)',
    keys: { 1: 'Kick/TR-606 Kick 01', 2: 'Kick/TR-606 Kick 02', 3: 'Snare/TR-606 Snare 01', 4: 'Snare/TR-606 Snare 02', 7: 'Hi Hat/TR-606 Hi Hat 01', 8: 'Hi Hat/TR-606 Hi Hat 02', 9: 'Open Hats/TR-606 Open Hat 01', 10: 'Open Hats/TR-606 Open Hat 02', 11: 'Cymbal/TR-606 Cymbal 01', 12: 'Cymbal/TR-606 Cymbal 02', 13: 'Tom/TR-606 Tom Lo 01', 14: 'Tom/TR-606 Tom Lo 02', 15: 'Tom/TR-606 Tom Hi 01', 16: 'Tom/TR-606 Tom Hi 02' },
  },
  {
    name: 'TR-626',
    folder: 'TR-626',
    machine: 'ROLAND TR-626 (1987)',
    keys: { 1: 'Kick/TR-626 Kick 1', 2: 'Kick/TR-626 Kick 2', 3: 'Snare/TR-626 Snare 1', 4: 'Snare/TR-626 Snare 2', 5: 'Rim Shot/TR-626 Rim 1', 6: 'Clap/TR-626 Clap 1', 7: 'Hi Hat/TR-626 HiHat', 8: 'Percs/TR-626 Shaker', 9: 'Cymbals/TR-626 Open Hat', 10: 'Percs/TR-626 Tambourine', 11: 'Cymbals/TR-626 Crash', 12: 'Cymbals/TR-626 Ride', 13: 'Tom/TR-626 Tom Lo 1', 14: 'Tom/TR-626 Tom Mid 1', 15: 'Tom/TR-626 Tom Hi 1', 16: 'Percs/TR-626 Cowbell' },
  },
  {
    name: 'TR-707',
    folder: 'TR-707',
    machine: 'ROLAND TR-707 (1985)',
    keys: { 1: 'Kick/TR-707 Kick 1', 2: 'Kick/TR-707 Kick 2', 3: 'Snare/TR-707 Snare 1', 4: 'Snare/TR-707 Snare 2', 5: 'Rimshot/TR-707 Rimshot 1', 6: 'Clap/TR-707 Clap 1', 7: 'Hi Hat/TR-707 Hi Hat 1', 8: 'Hi Hat/TR-707 Hi Hat 2', 9: 'Open Hats/TR-707 Open Hat 1', 10: 'Open Hats/TR-707 Open Hat 2', 11: 'Cymbal/TR-707 Crash', 12: 'Cymbal/TR-707 Ride 1', 13: 'Tom/TR-707 Low Tom 1', 14: 'Tom/TR-707 Mid Tom 1', 15: 'Tom/TR-707 High Tom 1', 16: 'Cowbell/TR-707 Cowbell 1' },
  },
  {
    name: 'TR-808',
    folder: 'TR-808',
    machine: 'ROLAND TR-808 (1980)',
    keys: { 1: '[BD] Bass Drum (Kick)/TR-808 BD Kick 01', 2: '[BD] Bass Drum (808s)/TR-808 BD Short 808s 01', 3: '[SD] Snare Drum/TR-808 Snare 01', 4: '[SD] Snare Drum/TR-808 Snare 02', 5: '[RS] Rim Shot/TR-808 Rim Shot 01', 6: '[CP] Hand Clap/TR-808 Clap 01', 7: '[CH] Closed Hat/TR-808 Closed Hat 01', 8: '[CH] Closed Hat/TR-808 Closed Hat 02', 9: '[OH] Open Hat/TR-808 Open Hat 01', 10: '[OH] Open Hat/TR-808 Open Hat 02', 11: '[CY] Cymbal/TR-808 Cymbal 01', 12: '[CY] Cymbal/TR-808 Cymbal 02', 13: '[LT] Low Tom/TR-808 Low Tom 01', 14: '[MT] Mid Tom/TR-808 Mid Tom 01', 15: '[HT] Hi Tom/TR-808 Hi Tom 01', 16: '[CB] Cowbell/TR-808 Cowbell 01' },
  },
  {
    name: 'TR-808 Percussion',
    folder: 'TR-808',
    machine: 'ROLAND TR-808 (1980)',
    keys: { 1: '[BD] Bass Drum (808s)/TR-808 BD Mid 808s 01', 2: '[BD] Bass Drum (808s)/TR-808 BD Saturated 808s 01', 3: '[SD] Snare Drum/TR-808 Snare 03', 4: '[RS] Rim Shot/TR-808 Rim Shot 02', 5: '[CL] Clave/TR-808 Clave 01', 6: '[CP] Hand Clap/TR-808 Clap 02', 7: '[MA] Maracas/TR-808 Maraca 01', 8: '[MA] Maracas/TR-808 Maraca 02', 9: '[LC] Low Conga/TR-808 Low Conga 01', 10: '[MC] Mid Conga/TR-808 Mid Conga 01', 11: '[HC] Hi Conga/TR-808 Hi Conga 01', 12: '[CB] Cowbell/TR-808 Cowbell 02', 13: '[LT] Low Tom/TR-808 Low Tom 02', 14: '[MT] Mid Tom/TR-808 Mid Tom 02', 15: '[HT] Hi Tom/TR-808 Hi Tom 02', 16: '[CY] Cymbal/TR-808 Cymbal 03' },
  },
  {
    name: 'TR-909',
    folder: 'TR-909',
    machine: 'ROLAND TR-909 (1983)',
    keys: { 1: 'Kicks/TR-909 Kick 01', 2: 'Kicks/TR-909 Kick 02', 3: 'Snares/TR-909 Snare 01', 4: 'Snares/TR-909 Snare 02', 5: 'Rim Shots/TR-909 Rim 01', 6: 'Claps/TR-909 Clap 01', 7: 'Closed Hats/TR-909 Closed Hat 01', 8: 'Closed Hats/TR-909 Closed Hat 02', 9: 'Open Hats/TR-909 Open Hat 01', 10: 'Open Hats/TR-909 Open Hat 02', 11: 'Crash/TR-909 Crash 01', 12: 'Ride/TR-909 Ride 01', 13: 'Toms/TR-909 Tom 01', 14: 'Toms/TR-909 Tom 02', 15: 'Toms/TR-909 Tom 03', 16: 'Rim Shots/TR-909 Rim 02' },
  },
];

export function kitByName(name: string): KitSpec {
  const kit = KITS.find((k) => k.name === name);
  if (!kit) throw new Error(`No standard kit named "${name}"`);
  return kit;
}

function mono(channels: Float64Array[]): Float64Array {
  if (channels.length === 1) return channels[0];
  const out = new Float64Array(channels[0].length);
  for (const c of channels) for (let i = 0; i < out.length; i++) out[i] += c[i] / channels.length;
  return out;
}

/** Native samples as codes, cut at `capSeconds` with a fade so the cut is silent. */
function capped(native: Float64Array, capSeconds: number): Uint8Array {
  const cap = Math.min(native.length, Math.round(capSeconds * SAMPLE_RATE));
  const fade = Math.round(FADE_SECONDS * SAMPLE_RATE);
  const out = new Float64Array(cap);
  for (let i = 0; i < cap; i++) {
    const tail = cap - i;
    out[i] = Math.max(-1, Math.min(1, native[i])) * (tail < fade ? tail / fade : 1);
  }
  return encodeMulaw(out);
}

/** A synthesized hit standing in for a pack sample, as codes: cut where it falls silent, at most `capSeconds`. */
export function synthCodes(machine: string, rel: string, key: number, capSeconds: number): Uint8Array {
  const hit = synthHit(machine, basename(rel), key, capSeconds);
  return capped(hit, trimmedLength(hit, capSeconds) / SAMPLE_RATE);
}

/** The synthesized kit's display name and library folder: "TR-808 Percussion" is "Synth 808 Percussion". */
export function synthName(name: string): string {
  return name.replace(/^TR-/, 'Synth ');
}

/** A hit as native codes, cut at `capSeconds` with a fade so the cut is silent. */
export function loadCapped(path: string, capSeconds: number): { codes: Uint8Array; rate: number } {
  const wav = parseWav(new Uint8Array(readFileSync(path)));
  const native = wav.sampleRate === SAMPLE_RATE ? mono(wav.channels) : toNativeRate(mono(wav.channels), wav.sampleRate);
  return { codes: capped(native, capSeconds), rate: wav.sampleRate };
}

export interface BuiltKit {
  name: string;
  /** Sample ids are the hit's path under the pack, the same in every kit and project that uses it. */
  samples: ArchiveSample[];
  slices: (Clip | null)[];
  /** Codes stored on the device for the whole kit. */
  stored: number;
}

/**
 * A standard kit's hits, each cut at its key's cap, and the slices over them: synthesized
 * when no pack is given, else loaded from the TR pack folder.
 */
export function buildKit(spec: KitSpec, pack?: string): BuiltKit {
  const samples: ArchiveSample[] = [];
  const slices: (Clip | null)[] = new Array(16).fill(null);
  let stored = 0;
  machineOf(spec.machine);
  for (const [key, rel] of Object.entries(spec.keys)) {
    const k = Number(key);
    const cap = CAP_SECONDS[k] ?? DEFAULT_CAP_SECONDS;
    let codes: Uint8Array;
    let id: string;
    let sample: Omit<ArchiveSample, 'codes' | 'id'>;
    if (pack === undefined) {
      codes = synthCodes(spec.machine, rel, k, cap);
      id = `synth/${spec.machine}/${rel}`;
      sample = { name: synthName(basename(rel)), folder: synthName(spec.folder), sourceName: 'synthesized (scripts/drum-synth.ts)', sourceRate: SAMPLE_RATE };
    } else {
      const path = join(pack, spec.machine, `${rel}.wav`);
      const loaded = loadCapped(path, cap);
      codes = loaded.codes;
      id = `${spec.machine}/${rel}`;
      sample = { name: basename(rel), folder: spec.folder, sourceName: basename(path), sourceRate: loaded.rate };
    }
    samples.push({ id, codes, ...sample });
    slices[k - 1] = { sampleId: id, start: 0, end: codes.length };
    stored += codes.length;
  }
  return { name: pack === undefined ? synthName(spec.name) : spec.name, samples, slices, stored };
}
