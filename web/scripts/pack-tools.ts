/**
 * Shared tools for the project-pack generators: synthesized instruments at the device
 * rate, drum hits from the TR packs, pattern writing, the four-voice and memory checks,
 * and the zip. A pack generator describes songs; this file turns them into archives.
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { basename, join } from 'node:path';

import { zipSync } from 'fflate';

import { type ArchiveProject, type ArchiveSample, packProject } from '../src/core/archive';
import { SAMPLE_RATE, encodeMulaw } from '../src/core/mulaw';
import { applyModifications } from '../src/core/edits';
import { type Cell, emptyPattern, writeCell, writeEffects } from '../src/core/pattern';
import { type Clip, MEMORY_PAGES, compileProject, projectPages } from '../src/core/project';
import { toNativeRate } from '../src/core/resample';
import { emptyTemplateState } from '../src/core/template';
import { parseWav } from '../src/core/wav';
import { keySemitones } from '../src/app/laws';
import { initialPlaybackState, scheduleBar } from '../src/app/playback';
import { buildKit, kitByName, synthCodes } from './kit-tools';

export { D } from './kit-tools';

export const RATE = SAMPLE_RATE;
export const midiHz = (midi: number): number => 440 * 2 ** ((midi - 69) / 12);

/** A small deterministic generator, so a pack rebuilds byte for byte. */
export function rng(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 2 ** 32;
  };
}

// Building blocks

/** One-pole low-pass, the tape's or the synth's softness. */
export function lowpass(x: Float64Array, hz: number): Float64Array {
  const a = 1 - Math.exp((-2 * Math.PI * hz) / RATE);
  const out = new Float64Array(x.length);
  let y = 0;
  for (let i = 0; i < x.length; i++) {
    y += a * (x[i] - y);
    out[i] = y;
  }
  return out;
}

/** One-pole high-pass, to thin a stab. */
export function highpass(x: Float64Array, hz: number): Float64Array {
  const low = lowpass(x, hz);
  const out = new Float64Array(x.length);
  for (let i = 0; i < x.length; i++) out[i] = x[i] - low[i];
  return out;
}

/** Normalize to the peak with a gentle soft clip, and fade the tail out. */
export function finish(x: Float64Array, peak: number, fadeSeconds = 0.06): Float64Array {
  let max = 0;
  for (const v of x) max = Math.max(max, Math.abs(v));
  const fade = Math.round(fadeSeconds * RATE);
  const out = new Float64Array(x.length);
  for (let i = 0; i < x.length; i++) {
    const tail = x.length - i;
    const g = tail < fade ? tail / fade : 1;
    out[i] = Math.tanh((x[i] / (max || 1)) * 1.2 * peak) * g;
  }
  return out;
}

export function mixInto(mix: Float64Array, part: Float64Array, gain = 1): void {
  for (let i = 0; i < mix.length && i < part.length; i++) mix[i] += part[i] * gain;
}

/** Vinyl: sparse clicks and a faint noise floor. */
export function vinyl(n: number, seed: number, clicksPerSecond: number, floor: number): Float64Array {
  const random = rng(seed);
  const out = new Float64Array(n);
  let noise = 0;
  for (let i = 0; i < n; i++) {
    noise = 0.97 * noise + 0.03 * (random() * 2 - 1);
    out[i] = noise * floor * 8;
    if (random() < clicksPerSecond / RATE) {
      const amp = (0.3 + random() * 0.7) * floor * 40;
      for (let k = 0; k < 40 && i + k < n; k++) out[i + k] += amp * Math.exp(-k / 6) * (k % 2 ? -1 : 1);
    }
  }
  return out;
}

/** A band-limited sawtooth: harmonics to the Nyquist limit, each at 1/h. */
export function saw(hz: number, n: number, detune = 0): Float64Array {
  const out = new Float64Array(n);
  const f = hz * (1 + detune);
  const harmonics = Math.min(40, Math.floor(RATE / 2 / f));
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    let v = 0;
    for (let h = 1; h <= harmonics; h++) v += Math.sin(2 * Math.PI * f * h * t) / h;
    out[i] = v * 0.6;
  }
  return out;
}

// Instruments

/** An electric-piano note: a few decaying partials with a soft attack and a slow chorus. */
export function epNote(hz: number, seconds: number, level = 1): Float64Array {
  const n = Math.round(seconds * RATE);
  const out = new Float64Array(n);
  const partials = [
    { ratio: 1, amp: 1, tau: 1.3 },
    { ratio: 2, amp: 0.28, tau: 0.5 },
    { ratio: 3, amp: 0.07, tau: 0.35 },
    { ratio: 5.04, amp: 0.05, tau: 0.12 },
  ];
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const attack = Math.min(1, t / 0.004);
    let v = 0;
    for (const p of partials) v += p.amp * Math.exp(-t / p.tau) * Math.sin(2 * Math.PI * hz * p.ratio * t);
    v += 0.5 * Math.exp(-t / 1.3) * Math.sin(2 * Math.PI * (hz + 0.4) * t + 0.3);
    out[i] = v * attack * level;
  }
  return out;
}

/** A Rhodes chord with a vinyl texture: one voicing, transposed by the keys. */
export function rhodesChord(midis: number[], seconds: number, seed: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const mix = new Float64Array(n);
  midis.forEach((m, i) => mixInto(mix, epNote(midiHz(m), seconds, 1 - i * 0.08)));
  const soft = lowpass(mix, 5200);
  mixInto(soft, vinyl(n, seed, 6, 0.004));
  return finish(soft, 0.85);
}

/** A soul organ chord: drawbar harmonics with a slow tremolo, chopped at its length like a sampled loop. */
export function organChord(midis: number[], seconds: number, seed: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const mix = new Float64Array(n);
  const drawbars = [
    { ratio: 1, amp: 1 },
    { ratio: 2, amp: 0.7 },
    { ratio: 3, amp: 0.45 },
    { ratio: 4, amp: 0.3 },
    { ratio: 6, amp: 0.12 },
    { ratio: 8, amp: 0.08 },
  ];
  for (const m of midis) {
    const hz = midiHz(m);
    for (let i = 0; i < n; i++) {
      const t = i / RATE;
      const env = Math.min(1, t / 0.012) * Math.exp(-t / 1.6) * (1 + 0.1 * Math.sin(2 * Math.PI * 5.8 * t));
      let v = 0;
      for (const d of drawbars) v += d.amp * Math.sin(2 * Math.PI * hz * d.ratio * t);
      mix[i] += v * env;
    }
  }
  const soft = lowpass(mix, 4200);
  mixInto(soft, vinyl(n, seed, 8, 0.005));
  return finish(soft, 0.85, 0.04);
}

/** A bright piano stab: stretched harmonics that decay fast, with a hammer click, for jacking chords. */
export function pianoStab(midis: number[], seconds: number, seed: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const mix = new Float64Array(n);
  const random = rng(seed);
  for (const m of midis) {
    const hz = midiHz(m);
    const harmonics = Math.min(12, Math.floor(RATE / 2 / hz));
    for (let i = 0; i < n; i++) {
      const t = i / RATE;
      let v = 0;
      for (let h = 1; h <= harmonics; h++) {
        const stretch = 1 + 0.0004 * h * h;
        v += (Math.exp(-t * (2.2 + 0.9 * h)) / h ** 1.1) * Math.sin(2 * Math.PI * hz * h * stretch * t);
      }
      mix[i] += v * Math.min(1, t / 0.0015);
    }
  }
  // The hammer: a short burst of noise at the onset.
  for (let i = 0; i < Math.round(0.006 * RATE); i++) mix[i] += (random() * 2 - 1) * 0.3 * (1 - i / (0.006 * RATE));
  return finish(highpass(lowpass(mix, 9000), 120), 0.9, 0.03);
}

/** A string pad: three detuned sawtooths per note under a low-pass, with a slow swell. */
export function stringPad(midis: number[], seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const mix = new Float64Array(n);
  for (const m of midis) {
    for (const detune of [-0.006, 0, 0.006]) mixInto(mix, saw(midiHz(m), n, detune), 0.5);
  }
  const soft = lowpass(lowpass(mix, 2600), 2600);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    soft[i] *= Math.min(1, t / 0.03) * Math.exp(-t / 2.5);
  }
  return finish(soft, 0.8, 0.08);
}

/** A brass stab: sawtooths with the filter sweeping down over the first 150 ms. */
export function brassStab(midis: number[], seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const mix = new Float64Array(n);
  for (const m of midis) mixInto(mix, saw(midiHz(m), n, 0.003), 0.7);
  const bright = lowpass(mix, 4200);
  const dark = lowpass(mix, 1200);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const sweep = Math.exp(-t / 0.15);
    out[i] = (bright[i] * sweep + dark[i] * (1 - sweep)) * Math.min(1, t / 0.008) * Math.exp(-t / 0.5);
  }
  return finish(out, 0.85, 0.04);
}

/** A round sine bass with a plucked second harmonic. */
export function subBass(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const hz = midiHz(midi);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const env = Math.min(1, t / 0.003) * Math.exp(-t / 0.5);
    out[i] = env * (Math.sin(2 * Math.PI * hz * t) + 0.3 * Math.exp(-t / 0.15) * Math.sin(2 * Math.PI * hz * 2 * t));
  }
  return finish(lowpass(out, 1800), 0.9, 0.03);
}

/** A house bass: a sawtooth pluck under a closing filter. */
export function houseBass(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const raw = saw(midiHz(midi), n);
  const bright = lowpass(raw, 1400);
  const dark = lowpass(raw, 300);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const sweep = Math.exp(-t / 0.08);
    out[i] = (bright[i] * sweep + dark[i] * (1 - sweep)) * Math.min(1, t / 0.002) * Math.exp(-t / 0.35);
  }
  return finish(out, 0.9, 0.02);
}

/** A single Rhodes note with a little vinyl, for melodies. */
export function rhodesLead(midi: number, seconds: number, seed: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const soft = lowpass(epNote(midiHz(midi), seconds, 1), 6000);
  mixInto(soft, vinyl(n, seed, 3, 0.003));
  return finish(soft, 0.8);
}

/** A sine bleep with a touch of second harmonic, for machine melodies. */
export function bleep(midi: number, seconds: number): Float64Array {
  const n = Math.round(seconds * RATE);
  const hz = midiHz(midi);
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const t = i / RATE;
    const env = Math.min(1, t / 0.002) * Math.exp(-t / 0.3);
    out[i] = env * (Math.sin(2 * Math.PI * hz * t) + 0.2 * Math.sin(2 * Math.PI * hz * 2 * t));
  }
  return finish(out, 0.8, 0.02);
}

export function toSample(id: string, name: string, folder: string, samples: Float64Array): ArchiveSample {
  return { id, name, folder, codes: encodeMulaw(samples), sourceName: `${name}.synth`, sourceRate: RATE };
}

// Drums from the TR packs

export function loadHit(pack: string | undefined, rel: string, capSeconds: number): Uint8Array {
  // Without a pack, the hit is synthesized in its place (the machine is the path's first folder).
  if (pack === undefined) return synthCodes(rel.split('/')[0], rel, 1, capSeconds);
  const wav = parseWav(new Uint8Array(readFileSync(join(pack, `${rel}.wav`))));
  const mono = wav.channels.length === 1 ? wav.channels[0] : wav.channels[0].map((_, i) => wav.channels.reduce((s, c) => s + c[i], 0) / wav.channels.length);
  const native = wav.sampleRate === RATE ? mono : toNativeRate(mono, wav.sampleRate);
  const cap = Math.min(native.length, Math.round(capSeconds * RATE));
  const out = new Float64Array(cap);
  const fade = Math.round(0.04 * RATE);
  for (let i = 0; i < cap; i++) {
    const tail = cap - i;
    out[i] = Math.max(-1, Math.min(1, native[i])) * (tail < fade ? tail / fade : 1);
  }
  return encodeMulaw(out);
}

// Keys

/** The key that plays a melodic sample `semitones` from its own pitch, or null when no key does. */
export function keyFor(semitones: number): number | null {
  for (let key = 1; key <= 16; key++) if (keySemitones(key) === semitones) return key;
  return null;
}

export function mustKey(semitones: number, what: string): number {
  const key = keyFor(semitones);
  if (key === null) throw new Error(`${what}: no key plays ${semitones} semitones from the sample`);
  return key;
}

// Songs

export interface Note {
  step: number;
  sound: number;
  key: number;
  /** Pitch code, 13 being the key's own pitch; one semitone per code, with the device's glide into it. */
  pitch?: number;
  volume?: number;
  filter?: number;
  resonance?: number;
  /** A melodic note's length in steps (1..14), or a drum note's retrigger count (2, 3, 4, 6, 8); the default plays full and once. */
  timing?: number;
}

export interface Colour {
  volume: number;
  filter: number;
  resonance?: number;
}

/** A drum sound's kit: one of the standard kits by name, with the windows of some keys shortened for this project where the voices need it. */
export interface PackKit {
  kit: string;
  trim?: Record<number, number>;
}

/** The library folder a synthesized sound belongs to, from its name. */
export function instrumentFolder(name: string): string {
  const n = name.toLowerCase();
  if (/bass|reese|sub|808/.test(n)) return 'Bass';
  if (/pad|string/.test(n)) return 'Pads';
  if (/brass|stab/.test(n)) return 'Stabs';
  if (/rhodes|organ|piano|skank|keys/.test(n)) return 'Keys';
  return 'Leads';
}

export interface SongSpec {
  name: string;
  tempo: number;
  swing: number;
  /** Melodic sounds 1..8 by slot: a sample each, synthesized, or a drum hit from the pack to play across the keys; the folder defaults to the instrument's. */
  melodic: Partial<Record<number, { id: string; name: string; samples?: Float64Array; hit?: [string, number]; folder?: string }>>;
  /** Drum sounds 9..16 by slot, each a standard kit. */
  kits: Partial<Record<number, PackKit>>;
  /** Default volume and filter per sound, written on every note. */
  colour: Record<number, Colour>;
  /** The bars, each a list of notes; bar i is pattern i + 1. */
  bars: Note[][];
  /** Punch-in effects per bar (by bar index), sixteen FX keys or nulls. */
  effects?: Record<number, (number | null)[]>;
  chain: number[];
}

export function pattern(notes: Note[], colour: Record<number, Colour>): Uint8Array {
  const data = emptyPattern();
  for (const n of notes) {
    const c = colour[n.sound];
    if (!c) throw new Error(`No colour for sound ${n.sound}`);
    const cell: Cell = { key: n.key, pitch: n.pitch ?? 13, volume: n.volume ?? c.volume, filter: n.filter ?? c.filter, resonance: n.resonance ?? c.resonance ?? 1, timing: n.timing };
    writeCell(data, n.step, n.sound, cell);
  }
  return data;
}

export function buildSong(spec: SongSpec, pack?: string): { project: ArchiveProject; samples: ArchiveSample[] } {
  if (spec.bars.length > 16) throw new Error(`${spec.name}: ${spec.bars.length} bars, 16 patterns at most`);
  const samples: ArchiveSample[] = [];
  const melodic: (Clip | null)[] = new Array(8).fill(null);
  for (const [slot, sound] of Object.entries(spec.melodic)) {
    if (!sound) continue;
    const folder = sound.folder ?? instrumentFolder(sound.name);
    const sample: ArchiveSample = sound.hit
      ? { id: sound.id, name: `${spec.name} ${sound.name}`, folder, codes: loadHit(pack, sound.hit[0], sound.hit[1]), sourceName: pack === undefined ? 'synthesized (scripts/drum-synth.ts)' : `${basename(sound.hit[0])}.wav`, sourceRate: pack === undefined ? RATE : 44100 }
      : toSample(sound.id, `${spec.name} ${sound.name}`, folder, sound.samples!);
    samples.push(sample);
    melodic[Number(slot) - 1] = { sampleId: sound.id, start: 0, end: sample.codes.length };
  }
  // The drums: standard kits, their samples listed once however many sounds share a kit, with this project's trims on the windows.
  const drums: ({ slices: (Clip | null)[] } | null)[] = new Array(8).fill(null);
  const kitNames: (string | null)[] = new Array(8).fill(null);
  const listed = new Set<string>();
  for (const [slot, kit] of Object.entries(spec.kits)) {
    if (!kit) continue;
    const built = buildKit(kitByName(kit.kit), pack);
    for (const sample of built.samples) {
      if (listed.has(sample.id)) continue;
      listed.add(sample.id);
      samples.push(sample);
    }
    const slices = built.slices.map((slice, i) => {
      if (!slice) return null;
      const trim = kit.trim?.[i + 1];
      return trim === undefined ? slice : { ...slice, end: Math.min(slice.end, Math.round(trim * RATE)) };
    });
    drums[Number(slot) - 9] = { slices };
    kitNames[Number(slot) - 9] = built.name;
  }
  const patterns = Array.from({ length: 16 }, () => emptyPattern());
  spec.bars.forEach((notes, i) => {
    patterns[i] = pattern(notes, spec.colour);
    const fx = spec.effects?.[i];
    if (fx) writeEffects(patterns[i], fx);
  });
  return { project: { name: spec.name, tempo: spec.tempo, swing: spec.swing, chain: spec.chain, melodic, drums, patterns, kitNames }, samples };
}

/** The file-safe, stable identity of a pack: "Rainy Rhodes" is "rainy-rhodes". */
export function slugOf(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

export interface PackFacts {
  name: string;
  slug: string;
  file: string;
  tempo: number;
  swing: number;
  bars: number;
  patterns: number;
  samples: number;
  pages: number;
  bytes: number;
  description: string;
}

/** Check a song against the device's four voices and memory, write its zip, and describe it. Throws on a dropped note. */
export async function writePack(spec: SongSpec, pack: string | undefined, out: string): Promise<PackFacts> {
  const { project, samples } = buildSong(spec, pack);
  // Resolved as the app resolves: with each sample's edits applied.
  const rendered = new Map(samples.map((s) => [s.id, applyModifications(s.codes, s.mods)]));
  const resolve = (id: string) => rendered.get(id)!;
  const core = { tempo: project.tempo, swing: project.swing, chain: project.chain, melodic: project.melodic, drums: project.drums, patterns: project.patterns };
  const pages = projectPages(core, resolve);
  if (pages > MEMORY_PAGES) throw new Error(`${spec.name}: ${pages} pages exceed the device's ${MEMORY_PAGES}`);
  compileProject(core, resolve, emptyTemplateState());
  let state = initialPlaybackState();
  let time = 0;
  const drops: string[] = [];
  const sounding: { sound: number; from: number; to: number }[] = [];
  const stepSeconds = 60 / project.tempo / 4;
  project.chain.forEach((p, bar) => {
    const result = scheduleBar(core, (id) => resolve(id).length, p - 1, time, state);
    state = result.state;
    for (const e of result.events) sounding.push({ sound: e.sound, from: e.time, to: e.time + e.duration });
    for (const d of result.dropped) {
      const at = time + (d.step - 1) * stepSeconds;
      const busy = sounding.filter((v) => v.from <= at && v.to > at + 0.1).map((v) => `${v.sound}@${((v.from - time) / stepSeconds + 1).toFixed(1)}→${((v.to - time) / stepSeconds + 1).toFixed(1)}`);
      drops.push(`bar ${bar + 1} (pattern ${p}) step ${d.step} sound ${d.sound} [busy: ${busy.join(' ')}]`);
    }
    time += stepSeconds * 16;
  });
  if (drops.length) throw new Error(`${spec.name}: voices dropped at ${drops.join('; ')}`);
  const files = await packProject(project, samples);
  const input: Record<string, Uint8Array> = {};
  for (const [p, b] of files) input[p] = b;
  const bytes = zipSync(input, { level: 6 });
  const file = join(out, `${slugOf(spec.name)}.sosample.zip`);
  writeFileSync(file, bytes);
  return {
    name: spec.name,
    slug: slugOf(spec.name),
    file: basename(file),
    tempo: project.tempo,
    swing: project.swing,
    bars: project.chain.length,
    patterns: spec.bars.length,
    samples: samples.length,
    pages,
    bytes: bytes.length,
    description: `${spec.name}: ${project.chain.length} bars at ${project.tempo} BPM, ${spec.bars.length} patterns, ${samples.length} samples, ${pages} pages → ${basename(file)}`,
  };
}
