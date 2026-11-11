/**
 * Project and kit archives: a human-readable JSON file plus every sample as a mu-law WAV,
 * which the app exports and reads back. The JSON states everything except the audio in
 * decoded form (notes, effects, windows in codes, edits), so a text editor can read it,
 * and the WAVs hold the native codes byte for byte, so reimport is exact.
 *
 * This module works on in-memory files (path to bytes); the app zips them.
 */

import { type Modifications, isUnmodified, noModifications } from './edits';
import { MAX_CHAIN } from './globals';
import { SAMPLE_RATE } from './mulaw';
import { type Cell, STEPS, SOUNDS, auxByte, cellOffsets, emptyPattern, readCell, readEffects, writeCell, writeEffects } from './pattern';
import type { Clip, DrumTrack } from './project';

export const PROJECT_FORMAT = 'sosample-project';
export const KIT_FORMAT = 'sosample-kit';
export const ARCHIVE_VERSION = 1;
/** WAV headers hold an integer rate; the JSON carries the exact one. */
export const WAV_RATE = 23438;

/** The files of an archive, by path. */
export type ArchiveFiles = Map<string, Uint8Array>;

export interface ArchiveSample {
  id: string;
  name: string;
  folder: string;
  codes: Uint8Array;
  mods?: Modifications;
  sourceName: string;
  sourceRate: number;
}

export interface ArchiveProject {
  name: string;
  tempo: number;
  swing: number;
  chain: number[];
  melodic: (Clip | null)[];
  drums: (DrumTrack | null)[];
  patterns: Uint8Array[];
  kitNames?: (string | null)[];
}

export interface ArchiveKit {
  name: string;
  slices: (Clip | null)[];
}

/** A sample read from an archive; `file` is its path, which the clips use as their sampleId until the app assigns ids. */
export interface UnpackedSample {
  file: string;
  name: string;
  folder: string;
  codes: Uint8Array;
  mods?: Modifications;
  sourceName: string;
  sourceRate: number;
  sha256: string;
}

// The JSON shapes.

interface SampleJson {
  file: string;
  name: string;
  folder: string;
  codes: number;
  sha256: string;
  source: { name: string; rate: number };
  edits?: Modifications;
}

interface ClipJson {
  sample: string;
  start: number;
  end: number;
}

interface NoteJson {
  step: number;
  sound: number;
  /** null: a parameter lock without a note. */
  key: number | null;
  pitch?: number;
  volume?: number;
  filter?: number;
  resonance?: number;
  bit5?: number;
  /** The note's auxiliary byte, only when the device wrote one the app would not. */
  aux?: number;
}

export interface PatternJson {
  effects: (number | null)[];
  notes: NoteJson[];
}

interface DrumJson {
  name?: string;
  keys?: Record<string, ClipJson>;
}

interface ProjectJson {
  format: string;
  version: number;
  name: string;
  tempo: number;
  swing: number;
  chain: number[];
  sampleRate: number;
  samples: SampleJson[];
  /** "1".."8": a clip; "9".."16": a kit. */
  sounds: Record<string, ClipJson | DrumJson>;
  patterns: PatternJson[];
}

interface KitJson {
  format: string;
  version: number;
  name: string;
  sampleRate: number;
  samples: SampleJson[];
  keys: Record<string, ClipJson>;
}

// Patterns

/** The notes and step effects of a pattern; parameters at 0 (no lock) are left out. */
export function patternToJson(data: Uint8Array): PatternJson {
  const notes: NoteJson[] = [];
  for (let step = 1; step <= STEPS; step++) {
    for (let sound = 1; sound <= SOUNDS; sound++) {
      const cell = readCell(data, step, sound);
      if (!cell) continue;
      const note: NoteJson = { step, sound, key: cell.key };
      for (const p of ['pitch', 'volume', 'filter', 'resonance'] as const) if (cell[p]) note[p] = cell[p];
      if (cell.bit5) note.bit5 = cell.bit5;
      const aux = data[cellOffsets(step, sound).aux];
      if (aux !== (cell.key === null ? 0 : auxByte(sound, cell.key))) note.aux = aux;
      notes.push(note);
    }
  }
  return { effects: readEffects(data), notes };
}

export function patternFromJson(json: PatternJson, where: string): Uint8Array {
  if (!json || typeof json !== 'object') throw new Error(`${where}: a pattern object is required`);
  const data = emptyPattern();
  if (!Array.isArray(json.effects) || json.effects.length !== STEPS) throw new Error(`${where}: sixteen step effects are required`);
  writeEffects(data, json.effects.map((fx) => (fx === null ? null : integer(fx, `${where} effect`))));
  if (!Array.isArray(json.notes)) throw new Error(`${where}: notes must be a list`);
  for (const n of json.notes) {
    const cell: Cell = {
      key: n.key === null || n.key === undefined ? null : integer(n.key, `${where} key`),
      pitch: optional(n.pitch, `${where} pitch`),
      volume: optional(n.volume, `${where} volume`),
      filter: optional(n.filter, `${where} filter`),
      resonance: optional(n.resonance, `${where} resonance`),
      bit5: optional(n.bit5, `${where} bit5`),
    };
    writeCell(data, integer(n.step, `${where} step`), integer(n.sound, `${where} sound`), cell);
    if (n.aux !== undefined) data[cellOffsets(n.step, n.sound).aux] = integer(n.aux, `${where} aux`) & 0xff;
  }
  return data;
}

// Mu-law WAV

/**
 * The device's code for a level and the G.711 byte for the same level differ in layout:
 * the device sets bit 7 on positive levels and complements negative ones, where G.711
 * complements every byte. Each code maps to exactly one G.711 byte and back, so a WAV
 * written in G.711 plays correctly in standard players and still carries the codes exactly.
 */
export function g711FromCode(code: number): number {
  return code & 128 ? code & 127 : code ^ 255;
}

export function codeFromG711(byte: number): number {
  return byte & 128 ? byte ^ 255 : byte | 128;
}

/** Native codes as a mono 8-bit mu-law WAV (format 7) in standard G.711 bytes, with the fact chunk non-PCM formats carry. */
export function mulawWav(codes: Uint8Array, rate = WAV_RATE): Uint8Array {
  const dataSize = codes.length;
  const out = new Uint8Array(12 + 26 + 12 + 8 + dataSize + (dataSize & 1));
  const view = new DataView(out.buffer);
  const ascii = (offset: number, text: string) => {
    for (let i = 0; i < 4; i++) out[offset + i] = text.charCodeAt(i);
  };
  ascii(0, 'RIFF');
  view.setUint32(4, out.length - 8, true);
  ascii(8, 'WAVE');
  ascii(12, 'fmt ');
  view.setUint32(16, 18, true);
  view.setUint16(20, 7, true); // WAVE_FORMAT_MULAW
  view.setUint16(22, 1, true);
  view.setUint32(24, rate, true);
  view.setUint32(28, rate, true);
  view.setUint16(32, 1, true);
  view.setUint16(34, 8, true);
  view.setUint16(36, 0, true); // cbSize
  ascii(38, 'fact');
  view.setUint32(42, 4, true);
  view.setUint32(46, codes.length, true);
  ascii(50, 'data');
  view.setUint32(54, dataSize, true);
  for (let i = 0; i < codes.length; i++) out[58 + i] = g711FromCode(codes[i]);
  return out;
}

/** The device codes of a mono 8-bit mu-law WAV, mapped from its G.711 bytes. */
export function mulawCodesFromWav(bytes: Uint8Array): Uint8Array {
  return readMulawWav(bytes).codes;
}

/** The codes and the header's sample rate of a mono 8-bit mu-law WAV, as the archives store samples. */
export function readMulawWav(bytes: Uint8Array): { codes: Uint8Array; rate: number } {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const tag = (offset: number): string => String.fromCharCode(...bytes.subarray(offset, offset + 4));
  if (bytes.length < 12 || tag(0) !== 'RIFF' || tag(8) !== 'WAVE') throw new Error('not a RIFF/WAVE file');
  let offset = 12;
  let format = 0;
  let channels = 0;
  let bits = 0;
  let rate = 0;
  let data: Uint8Array | null = null;
  while (offset + 8 <= bytes.length) {
    const id = tag(offset);
    const size = view.getUint32(offset + 4, true);
    const body = offset + 8;
    if (id === 'fmt ') {
      if (body + 16 > bytes.length) throw new Error('WAV is truncated');
      format = view.getUint16(body, true);
      channels = view.getUint16(body + 2, true);
      rate = view.getUint32(body + 4, true);
      bits = view.getUint16(body + 14, true);
      if (format === 0xfffe && size >= 26) format = view.getUint16(body + 24, true);
    } else if (id === 'data') {
      data = bytes.subarray(body, Math.min(body + size, bytes.length));
    }
    offset = body + size + (size & 1);
  }
  if (!data) throw new Error('WAV has no data chunk');
  if (format !== 7 || channels !== 1 || bits !== 8) throw new Error('not a mono 8-bit mu-law WAV');
  const codes = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) codes[i] = codeFromG711(data[i]);
  return { codes, rate };
}

// Samples

export async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', bytes as BufferSource);
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('');
}

/** "samples/<name>.wav", made safe for file systems and unique within the archive. */
function fileNameFor(name: string, taken: Set<string>): string {
  const base =
    Array.from(name.replace(/[\\/:*?"<>|]/g, ' '))
      .filter((ch) => ch.charCodeAt(0) >= 32)
      .join('')
      .replace(/\s+/g, ' ')
      .trim() || 'sample';
  let file = `samples/${base}.wav`;
  for (let n = 2; taken.has(file.toLowerCase()); n++) file = `samples/${base} ${n}.wav`;
  taken.add(file.toLowerCase());
  return file;
}

async function packSamples(samples: ArchiveSample[], files: ArchiveFiles): Promise<{ entries: SampleJson[]; fileOf: Map<string, string> }> {
  const taken = new Set<string>();
  const entries: SampleJson[] = [];
  const fileOf = new Map<string, string>();
  for (const sample of samples) {
    const file = fileNameFor(sample.name, taken);
    fileOf.set(sample.id, file);
    const entry: SampleJson = {
      file,
      name: sample.name,
      folder: sample.folder,
      codes: sample.codes.length,
      sha256: await sha256Hex(sample.codes),
      source: { name: sample.sourceName, rate: sample.sourceRate },
    };
    if (sample.mods && !isUnmodified(sample.mods, sample.codes.length)) entry.edits = sample.mods;
    entries.push(entry);
    files.set(file, mulawWav(sample.codes));
  }
  return { entries, fileOf };
}

async function unpackSamples(entries: unknown, files: ArchiveFiles): Promise<UnpackedSample[]> {
  if (!Array.isArray(entries)) throw new Error('samples must be a list');
  const out: UnpackedSample[] = [];
  const seen = new Set<string>();
  for (const entry of entries as Partial<SampleJson>[]) {
    if (!entry || typeof entry !== 'object') throw new Error('Each sample entry must be an object');
    const file = text(entry.file, 'sample file');
    if (seen.has(file)) throw new Error(`${file} is listed twice`);
    seen.add(file);
    const bytes = files.get(file);
    if (!bytes) throw new Error(`${file} is missing from the archive`);
    let codes: Uint8Array;
    try {
      codes = mulawCodesFromWav(bytes);
    } catch (error) {
      throw new Error(`${file}: ${(error as Error).message}`);
    }
    if (entry.codes !== undefined && codes.length !== entry.codes) throw new Error(`${file}: ${codes.length} codes, but ${entry.codes} are listed`);
    const sha256 = await sha256Hex(codes);
    if (entry.sha256 !== undefined && entry.sha256 !== sha256) throw new Error(`${file}: the audio does not match its checksum`);
    const source = (entry.source ?? {}) as Partial<SampleJson['source']>;
    out.push({
      file,
      name: typeof entry.name === 'string' && entry.name ? entry.name : file.replace(/^samples\//, '').replace(/\.wav$/i, ''),
      folder: typeof entry.folder === 'string' ? entry.folder : '',
      codes,
      mods: entry.edits === undefined ? undefined : modifications(entry.edits, codes.length, `${file} edits`),
      sourceName: typeof source.name === 'string' ? source.name : file,
      sourceRate: typeof source.rate === 'number' ? source.rate : SAMPLE_RATE,
      sha256,
    });
  }
  return out;
}

function modifications(value: unknown, length: number, where: string): Modifications {
  if (!value || typeof value !== 'object') throw new Error(`${where}: an object is required`);
  const v = value as Partial<Modifications>;
  const base = noModifications(length);
  const mods: Modifications = {
    start: v.start === undefined ? base.start : integer(v.start, `${where} start`),
    end: v.end === undefined ? base.end : integer(v.end, `${where} end`),
    gainDb: v.gainDb === undefined ? 0 : bounded(v.gainDb, -24, 24, `${where} gainDb`),
    normalize: v.normalize === undefined ? false : boolean(v.normalize, `${where} normalize`),
    fadeIn: v.fadeIn === undefined ? 0 : ranged(v.fadeIn, 0, length, `${where} fadeIn`),
    fadeOut: v.fadeOut === undefined ? 0 : ranged(v.fadeOut, 0, length, `${where} fadeOut`),
    compressor: null,
  };
  // The ranges are the sample editor's: a ratio under 1 would make the compressor's maths blow up.
  if (v.compressor) {
    const c = v.compressor as Partial<NonNullable<Modifications['compressor']>>;
    mods.compressor = {
      thresholdDb: bounded(c.thresholdDb, -60, 0, `${where} compressor thresholdDb`),
      ratio: bounded(c.ratio, 1, 20, `${where} compressor ratio`),
      makeupDb: bounded(c.makeupDb, 0, 24, `${where} compressor makeupDb`),
    };
  }
  if (mods.start < 0 || mods.end > length || mods.end < mods.start) throw new Error(`${where}: trim ${mods.start}..${mods.end} lies outside the ${length} codes`);
  return mods;
}

// Clips

function clipJson(clip: Clip, fileOf: Map<string, string>): ClipJson {
  const sample = fileOf.get(clip.sampleId);
  if (!sample) throw new Error(`Sample ${clip.sampleId} is not in the library`);
  return { sample, start: clip.start, end: clip.end };
}

function clipFromJson(value: unknown, samples: Map<string, UnpackedSample>, where: string): Clip {
  if (!value || typeof value !== 'object') throw new Error(`${where}: a clip object is required`);
  const v = value as Partial<ClipJson>;
  const file = text(v.sample, `${where} sample`);
  const sample = samples.get(file);
  if (!sample) throw new Error(`${where}: ${file} is not among the archive's samples`);
  const start = integer(v.start, `${where} start`);
  const end = integer(v.end, `${where} end`);
  // A window past the sample's end is kept: device backups hold such windows, and the app reports them as they are.
  if (start < 0 || end < start) throw new Error(`${where}: window ${start}..${end} is not a range`);
  return { sampleId: file, start, end };
}

function keysJson(slices: (Clip | null)[], fileOf: Map<string, string>): Record<string, ClipJson> {
  const keys: Record<string, ClipJson> = {};
  slices.forEach((clip, k) => {
    if (clip) keys[String(k + 1)] = clipJson(clip, fileOf);
  });
  return keys;
}

function keysFromJson(value: unknown, samples: Map<string, UnpackedSample>, where: string): (Clip | null)[] {
  if (!value || typeof value !== 'object') throw new Error(`${where}: keys must be an object`);
  const slices: (Clip | null)[] = new Array(16).fill(null);
  for (const [key, clip] of Object.entries(value as Record<string, unknown>)) {
    const k = Number(key);
    if (!Number.isInteger(k) || k < 1 || k > 16) throw new Error(`${where}: key ${key} is not 1..16`);
    slices[k - 1] = clipFromJson(clip, samples, `${where} key ${k}`);
  }
  return slices;
}

/** The samples the clips reference, in library order; a reference to a sample not in the library throws. */
function referenced(clips: (Clip | null)[], samples: ArchiveSample[]): ArchiveSample[] {
  const ids = new Set<string>();
  for (const clip of clips) if (clip) ids.add(clip.sampleId);
  const found = samples.filter((s) => ids.has(s.id));
  for (const id of ids) if (!found.some((s) => s.id === id)) throw new Error(`Sample ${id} is not in the library`);
  return found;
}

// Projects

export async function packProject(project: ArchiveProject, samples: ArchiveSample[]): Promise<ArchiveFiles> {
  const files: ArchiveFiles = new Map();
  const clips = [...project.melodic, ...project.drums.flatMap((d) => d?.slices ?? [])];
  const { entries, fileOf } = await packSamples(referenced(clips, samples), files);
  const sounds: Record<string, ClipJson | DrumJson> = {};
  project.melodic.forEach((clip, i) => {
    if (clip) sounds[String(i + 1)] = clipJson(clip, fileOf);
  });
  project.drums.forEach((track, i) => {
    const name = project.kitNames?.[i] ?? null;
    if (!track && !name) return;
    const entry: DrumJson = {};
    if (name) entry.name = name;
    if (track) entry.keys = keysJson(track.slices, fileOf);
    sounds[String(i + 9)] = entry;
  });
  const json: ProjectJson = {
    format: PROJECT_FORMAT,
    version: ARCHIVE_VERSION,
    name: project.name,
    tempo: project.tempo,
    swing: project.swing,
    chain: project.chain,
    sampleRate: SAMPLE_RATE,
    samples: entries,
    sounds,
    patterns: project.patterns.map(patternToJson),
  };
  files.set('project.json', utf8(formatJson(json)));
  return files;
}

export async function unpackProject(files: ArchiveFiles): Promise<{ project: ArchiveProject; samples: UnpackedSample[] }> {
  const json = parseJson(files, 'project.json', PROJECT_FORMAT) as Partial<ProjectJson>;
  const samples = await unpackSamples(json.samples ?? [], files);
  const byFile = new Map(samples.map((s) => [s.file, s]));
  const sounds = (json.sounds ?? {}) as Record<string, unknown>;
  const melodic: (Clip | null)[] = new Array(8).fill(null);
  const drums: (DrumTrack | null)[] = new Array(8).fill(null);
  const kitNames: (string | null)[] = new Array(8).fill(null);
  for (const [key, value] of Object.entries(sounds)) {
    const sound = Number(key);
    if (!Number.isInteger(sound) || sound < 1 || sound > 16) throw new Error(`Sound ${key} is not 1..16`);
    if (sound <= 8) melodic[sound - 1] = clipFromJson(value, byFile, `Sound ${sound}`);
    else {
      if (!value || typeof value !== 'object') throw new Error(`Sound ${sound}: a kit object is required`);
      const kit = value as DrumJson;
      if (kit.name !== undefined) kitNames[sound - 9] = text(kit.name, `Sound ${sound} name`);
      if (kit.keys !== undefined) drums[sound - 9] = { slices: keysFromJson(kit.keys, byFile, `Sound ${sound}`) };
    }
  }
  if (!Array.isArray(json.patterns) || json.patterns.length !== 16) throw new Error('Sixteen patterns are required');
  const chain = Array.isArray(json.chain) ? json.chain.map((p) => integer(p, 'chain entry')) : [];
  for (const p of chain) if (p < 1 || p > 16) throw new Error(`Chain pattern ${p} is not 1..16`);
  // The device's chain holds 128 entries; a longer one would import and then fail at Send.
  if (chain.length > MAX_CHAIN) throw new Error(`The chain holds ${chain.length} patterns; the PO-33 holds at most ${MAX_CHAIN}`);
  const project: ArchiveProject = {
    name: typeof json.name === 'string' ? json.name : 'Imported project',
    tempo: ranged(json.tempo ?? 120, 60, 240, 'tempo'),
    swing: ranged(json.swing ?? 0, 0, 18, 'swing'),
    chain,
    melodic,
    drums,
    patterns: json.patterns.map((p, i) => patternFromJson(p as PatternJson, `Pattern ${i + 1}`)),
    kitNames: kitNames.some((n) => n) ? kitNames : undefined,
  };
  return { project, samples };
}

// Kits

export async function packKit(kit: ArchiveKit, samples: ArchiveSample[]): Promise<ArchiveFiles> {
  const files: ArchiveFiles = new Map();
  const { entries, fileOf } = await packSamples(referenced(kit.slices, samples), files);
  const json: KitJson = { format: KIT_FORMAT, version: ARCHIVE_VERSION, name: kit.name, sampleRate: SAMPLE_RATE, samples: entries, keys: keysJson(kit.slices, fileOf) };
  files.set('kit.json', utf8(formatJson(json)));
  return files;
}

export async function unpackKit(files: ArchiveFiles): Promise<{ kit: ArchiveKit; samples: UnpackedSample[] }> {
  const json = parseJson(files, 'kit.json', KIT_FORMAT) as Partial<KitJson>;
  const samples = await unpackSamples(json.samples ?? [], files);
  const byFile = new Map(samples.map((s) => [s.file, s]));
  const kit: ArchiveKit = { name: typeof json.name === 'string' && json.name ? json.name : 'Imported kit', slices: keysFromJson(json.keys ?? {}, byFile, 'Kit') };
  return { kit, samples };
}

// JSON helpers

function parseJson(files: ArchiveFiles, name: string, format: string): unknown {
  const bytes = files.get(name);
  if (!bytes) throw new Error(`The archive has no ${name}`);
  let json: unknown;
  try {
    json = JSON.parse(new TextDecoder().decode(bytes));
  } catch (error) {
    throw new Error(`${name}: ${(error as Error).message}`);
  }
  if (!json || typeof json !== 'object') throw new Error(`${name}: an object is required`);
  const header = json as { format?: unknown; version?: unknown };
  if (header.format !== format) throw new Error(`${name} is not a ${format} file`);
  if (typeof header.version !== 'number' || header.version > ARCHIVE_VERSION) throw new Error(`${name}: version ${String(header.version)} is newer than this app reads`);
  return json;
}

/** Indented JSON with each note, effect list and chain on one line, so patterns stay readable. */
function formatJson(json: unknown): string {
  return JSON.stringify(json, null, 2)
    .replace(/\{\s+"step":[^{}]*\}/g, (m) => m.replace(/\s+/g, ' '))
    .replace(/"(effects|chain)": \[[^\]]*\]/g, (m) => m.replace(/\s+/g, ' ').replace('[ ', '[').replace(' ]', ']'));
}

function utf8(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

function integer(value: unknown, where: string): number {
  if (typeof value !== 'number' || !Number.isInteger(value)) throw new Error(`${where} must be an integer, got ${JSON.stringify(value)}`);
  return value;
}

/** An integer within the device's range for the field. */
function ranged(value: unknown, low: number, high: number, where: string): number {
  const n = integer(value, where);
  if (n < low || n > high) throw new Error(`${where} must be ${low}..${high}, got ${n}`);
  return n;
}

function optional(value: unknown, where: string): number {
  return value === undefined ? 0 : integer(value, where);
}

function number(value: unknown, where: string): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`${where} must be a number, got ${JSON.stringify(value)}`);
  return value;
}

function bounded(value: unknown, low: number, high: number, where: string): number {
  const n = number(value, where);
  if (n < low || n > high) throw new Error(`${where} must be ${low}..${high}, got ${n}`);
  return n;
}

function boolean(value: unknown, where: string): boolean {
  if (typeof value !== 'boolean') throw new Error(`${where} must be true or false`);
  return value;
}

function text(value: unknown, where: string): string {
  if (typeof value !== 'string' || !value) throw new Error(`${where} must be a non-empty string`);
  return value;
}
