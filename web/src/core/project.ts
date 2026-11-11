/**
 * The project model and its translation to and from a device state.
 *
 * A project is one PO-33 state: tempo, swing, chain, eight melodic tracks, eight drum
 * tracks and sixteen patterns. Tracks hold clips: a library sample id plus a window in
 * native codes. The compile step lays samples out the way the device does:
 *
 * - A sample used by melodic tracks is stored once, under the lowest melodic sound that
 *   uses it; every other track using it, melodic or drum, references that buffer with its
 *   own window (the factory content does this between Sounds 1, 2, 3, 8 and the drum
 *   slices of Sounds 9 and 10).
 * - Samples used only by a drum track are concatenated into that track's kit buffer,
 *   each distinct sample once, under the track's key-1 sound, as the device records a
 *   kit; the slices are windows into it. Key 1 is always in the kit buffer when one
 *   exists, since the buffer lives under its sound id.
 * - A sample already in an earlier drum track's kit buffer is referenced there by later
 *   drum tracks instead of stored again, so the same kit on several drum sounds is stored
 *   once; key 1 leads a track's own buffer whenever the track stores anything. Verified
 *   on the device in kit-sharing-001 (docs/kit-sharing-results.md). `shareKitSamples:
 *   false` gives the earlier layout, one copy per drum track.
 * - An empty slice has no record at all, as empty slots have in a device backup.
 *
 * Everything the device stores but the model does not describe (the first global
 * record, bytes 131 onwards of the second) comes from the empty-device template.
 */

import { readChain, readSwing, readTempo, writeChain, writeSwing, writeTempo } from './globals';
import { PAGE, type DeviceState, type SoundRecord, cloneState, SOUND_IDS } from './state';

export const MEMORY_PAGES = 241;
/** Shortest sample buffer the app keeps; imported buffers are padded to it. */
export const MIN_CLIP_CODES = 128;
/**
 * Shortest window the clip editor lets a user set. Compiling accepts any window that does
 * not end before it starts: the device writes empty ones itself. Exploratory observation,
 * 2026-11-07: a browser-recorded backup held Sound 9 key 15 at 49856..49856, at the end of
 * the kit's buffer, with key 16 having no record. Trimming on the device bottoms out at 79
 * codes for a melodic sound and 127 for a drum key (drum9-key1-trim-min), and windows
 * shorter than 79 codes have not yet been played by the device from a compiled restore.
 */
export const MIN_WINDOW_CODES = 1;
export const MELODIC_SLOTS = [1, 2, 3, 4, 5, 6, 7, 8];
export const DRUM_SLOTS = [9, 10, 11, 12, 13, 14, 15, 16];

export interface Clip {
  sampleId: string;
  /** Window in native codes of the sample, start inclusive, end exclusive. */
  start: number;
  end: number;
}

export interface DrumTrack {
  /** Sixteen slices, key 1 first. */
  slices: (Clip | null)[];
}

export interface Project {
  tempo: number;
  swing: number;
  chain: number[];
  /** Slots 1..8. */
  melodic: (Clip | null)[];
  /** Slots 9..16. */
  drums: (DrumTrack | null)[];
  /** Sixteen raw 1032-byte patterns. */
  patterns: Uint8Array[];
}

/** Native mu-law codes of a library sample, with its modifications applied. */
export type SampleResolver = (sampleId: string) => Uint8Array;

export class MemoryLimitError extends Error {
  readonly pages: number;

  constructor(pages: number) {
    super(`The project needs ${pages} pages of sample memory; the device has ${MEMORY_PAGES}`);
    this.pages = pages;
  }
}

export function melodicSoundId(slot: number): number {
  return slot - 1;
}

export function drumSoundIds(slot: number): number[] {
  const first = 8 + 16 * (slot - 9);
  return Array.from({ length: 16 }, (_, k) => first + k);
}

export function pagesFor(codes: number): number {
  return Math.ceil(codes / PAGE);
}

function padToPages(codes: Uint8Array): Uint8Array {
  const out = new Uint8Array(pagesFor(codes.length) * PAGE);
  out.set(codes);
  return out;
}

function checkClip(clip: Clip, length: number, where: string): void {
  if (!Number.isInteger(clip.start) || !Number.isInteger(clip.end) || clip.start < 0 || clip.end > length) {
    throw new Error(`${where}: window ${clip.start}..${clip.end} lies outside the sample (${length} codes)`);
  }
  if (clip.end < clip.start) {
    throw new Error(`${where}: window ${clip.start}..${clip.end} ends before it starts`);
  }
}

/**
 * Whether drum tracks reference samples stored in an earlier drum track's kit buffer.
 * Verified on the device in kit-sharing-001 (docs/kit-sharing-results.md).
 */
export const SHARE_KIT_SAMPLES = true;

export interface LayoutOptions {
  /** Reference a sample already in an earlier kit buffer instead of storing it again; default SHARE_KIT_SAMPLES. */
  shareKitSamples?: boolean;
}

/** Sample memory the project would use, in pages. */
export function projectPages(project: Project, resolve: SampleResolver, options: LayoutOptions = {}): number {
  return layoutSounds(project, resolve, options).pages;
}

/** One buffer the device will hold: a library sample stored under a melodic sound, or inside a kit. */
export interface MemoryRow {
  sampleId: string;
  /** "Sound 1" for a melodic owner, "Sound 9 kit" for a part of a kit buffer. */
  storedIn: string;
  /** Codes stored: the whole sample under a melodic owner, up to the furthest window end in a kit. */
  codes: number;
  pages: number;
  /** Every clip that plays from this buffer, as "Sound 2" or "Sound 9 key 3". */
  usedBy: string[];
  /** The clips' windows into the stored codes, in the same order as usedBy. */
  windows: { start: number; end: number }[];
}

/** What the project stores on the device, one row per buffer in layout order, and the page total. */
export function memorySummary(project: Project, resolve: SampleResolver, options: LayoutOptions = {}): { rows: MemoryRow[]; pages: number } {
  const { rows, pages } = layoutSounds(project, resolve, options);
  return { rows, pages };
}

export function compileProject(project: Project, resolve: SampleResolver, template: DeviceState, options: LayoutOptions = {}): DeviceState {
  const state = cloneState(template);
  writeTempo(state.globals[1], project.tempo);
  writeSwing(state.globals[1], project.swing);
  writeChain(state.globals[1], project.chain.length ? project.chain : [1]);
  if (project.patterns.length !== 16 || project.patterns.some((p) => p.length !== 1032)) {
    throw new Error('A project holds sixteen 1032-byte patterns');
  }
  state.patterns = project.patterns.map((p) => p.slice());
  const { sounds, pages } = layoutSounds(project, resolve, options);
  if (pages > MEMORY_PAGES) throw new MemoryLimitError(pages);
  state.sounds = sounds;
  return state;
}

function layoutSounds(project: Project, resolve: SampleResolver, options: LayoutOptions = {}): { sounds: (SoundRecord | null)[]; pages: number; rows: MemoryRow[] } {
  const shareKits = options.shareKitSamples ?? SHARE_KIT_SAMPLES;
  /** With kit sharing: where an earlier kit stored a sample, its owner id, offset in the buffer and codes stored. */
  const kitStored = new Map<string, { owner: number; offset: number; end: number; row: MemoryRow }>();
  if (project.melodic.length !== 8 || project.drums.length !== 8) throw new Error('A project has eight melodic and eight drum slots');
  const sounds: (SoundRecord | null)[] = new Array(SOUND_IDS).fill(null);
  const samples = new Map<string, Uint8Array>();
  const sample = (id: string): Uint8Array => {
    let codes = samples.get(id);
    if (!codes) {
      codes = resolve(id);
      samples.set(id, codes);
    }
    return codes;
  };
  const owners = new Map<string, number>();
  const rows: MemoryRow[] = [];
  const rowOf = new Map<string, MemoryRow>();
  let pages = 0;
  MELODIC_SLOTS.forEach((slot, index) => {
    const clip = project.melodic[index];
    if (!clip) return;
    const codes = sample(clip.sampleId);
    checkClip(clip, codes.length, `Sound ${slot}`);
    const id = melodicSoundId(slot);
    const owner = owners.get(clip.sampleId);
    if (owner === undefined) {
      owners.set(clip.sampleId, id);
      const buffer = padToPages(codes);
      pages += buffer.length / PAGE;
      sounds[id] = { start: clip.start, end: clip.end, owner: id, codes: buffer };
      const row = { sampleId: clip.sampleId, storedIn: `Sound ${slot}`, codes: codes.length, pages: buffer.length / PAGE, usedBy: [`Sound ${slot}`], windows: [{ start: clip.start, end: clip.end }] };
      rows.push(row);
      rowOf.set(clip.sampleId, row);
    } else {
      sounds[id] = { start: clip.start, end: clip.end, owner, codes: new Uint8Array(0) };
      const row = rowOf.get(clip.sampleId)!;
      row.usedBy.push(`Sound ${slot}`);
      row.windows.push({ start: clip.start, end: clip.end });
    }
  });
  DRUM_SLOTS.forEach((slot, index) => {
    const track = project.drums[index];
    if (!track) return;
    if (track.slices.length !== 16) throw new Error(`Sound ${slot}: a drum track has sixteen slices`);
    const ids = drumSoundIds(slot);
    track.slices.forEach((clip, k) => {
      if (clip) checkClip(clip, sample(clip.sampleId).length, `Sound ${slot} key ${k + 1}`);
    });
    // Slices that cannot reference a melodic owner (or, with kit sharing, an earlier kit
    // holding enough of the sample) go into the kit buffer; key 1 joins them whenever a
    // kit buffer exists, because the buffer is stored under its id.
    const sharedFrom = (clip: Clip): { owner: number; offset: number; end: number; row: MemoryRow } | undefined => {
      if (!shareKits) return undefined;
      const stored = kitStored.get(clip.sampleId);
      return stored && clip.end <= stored.end ? stored : undefined;
    };
    let embedded = new Set<string>();
    track.slices.forEach((clip) => {
      if (clip && !owners.has(clip.sampleId) && !sharedFrom(clip)) embedded.add(clip.sampleId);
    });
    if (embedded.size && track.slices[0]) {
      // With sharing, key 1's sample leads its buffer, so key 1 starts at code 0 as every
      // verified kit does; without it the order is the slices' own, as before.
      embedded = shareKits ? new Set([track.slices[0].sampleId, ...embedded]) : embedded.add(track.slices[0].sampleId);
    }
    const offsets = new Map<string, number>();
    const parts: Uint8Array[] = [];
    let length = 0;
    const kitRows = new Map<string, MemoryRow>();
    for (const sampleId of embedded) {
      let end = 0;
      for (const clip of track.slices) if (clip && clip.sampleId === sampleId) end = Math.max(end, clip.end);
      offsets.set(sampleId, length);
      parts.push(sample(sampleId).subarray(0, end));
      const row = { sampleId, storedIn: `Sound ${slot} kit`, codes: end, pages: 0, usedBy: [] as string[], windows: [] as { start: number; end: number }[] };
      rows.push(row);
      kitRows.set(sampleId, row);
      // Later kits find a sample in the kit that stores the most of it, so one long copy serves every shorter use
      // after it. The buffer lives under that kit's key 1, so earlier references to another copy stay valid.
      const stored = kitStored.get(sampleId);
      if (!stored || end > stored.end) kitStored.set(sampleId, { owner: ids[0], offset: length, end, row });
      length += end;
    }
    // A buffer of no codes is no layout the device has been seen to accept: a kit whose own windows are all empty is refused.
    if (embedded.size && length === 0) throw new Error(`Sound ${slot}: the kit's windows are all empty; give key 1 a window of at least one code`);
    let kit: Uint8Array | null = null;
    if (embedded.size) {
      kit = new Uint8Array(pagesFor(length) * PAGE);
      let offset = 0;
      for (const part of parts) {
        kit.set(part, offset);
        offset += part.length;
      }
      pages += kit.length / PAGE;
      // The parts of a kit share its whole pages: each row shows its share by length, to a tenth, so a kit's rows add
      // up to the pages it takes (a lone 0.2 s kick in a two-page kit shows 2, not 1).
      const kitPages = kit.length / PAGE;
      for (const row of kitRows.values()) row.pages = length ? Math.round(((kitPages * row.codes) / length) * 10) / 10 : 0;
    }
    track.slices.forEach((clip, k) => {
      if (!clip) return;
      const id = ids[k];
      const offset = offsets.get(clip.sampleId);
      const shared = offset === undefined && !owners.has(clip.sampleId) ? sharedFrom(clip) : undefined;
      const row = (kitRows.get(clip.sampleId) ?? shared?.row ?? rowOf.get(clip.sampleId))!;
      row.usedBy.push(`Sound ${slot} key ${k + 1}`);
      row.windows.push({ start: clip.start, end: clip.end });
      if (offset !== undefined) {
        sounds[id] = { start: clip.start + offset, end: clip.end + offset, owner: ids[0], codes: k === 0 && kit ? kit : new Uint8Array(0) };
      } else if (shared) {
        // A window into the earlier kit's buffer, where the sample starts at its offset.
        sounds[id] = { start: clip.start + shared.offset, end: clip.end + shared.offset, owner: shared.owner, codes: new Uint8Array(0) };
      } else {
        sounds[id] = { start: clip.start, end: clip.end, owner: owners.get(clip.sampleId)!, codes: new Uint8Array(0) };
      }
    });
    if (kit && !track.slices[0]) {
      throw new Error(`Sound ${slot}: key 1 must hold a slice when the kit stores samples of its own`);
    }
  });
  return { sounds, pages, rows };
}

export interface ImportedProject {
  project: Project;
  /** New library samples: one per sample buffer in the backup, trimmed to the codes any window reaches. */
  samples: Map<string, Uint8Array>;
}

/** Sample id used for a buffer found under a device sound id. */
export function importedSampleId(ownerId: number): string {
  return `device-sound-${ownerId}`;
}

export function importProject(state: DeviceState): ImportedProject {
  const reach = new Map<number, number>();
  state.sounds.forEach((record) => {
    if (!record) return;
    reach.set(record.owner, Math.max(reach.get(record.owner) ?? 0, record.end));
  });
  const samples = new Map<string, Uint8Array>();
  state.sounds.forEach((record, id) => {
    if (!record || !record.codes.length) return;
    samples.set(importedSampleId(id), record.codes.slice(0, Math.max(reach.get(id) ?? 0, MIN_CLIP_CODES)));
  });
  const clipOf = (record: SoundRecord | null, where: string): Clip | null => {
    if (!record) return null;
    const sampleId = importedSampleId(record.owner);
    if (!samples.has(sampleId)) throw new Error(`${where} references sound ${record.owner}, which holds no sample`);
    return { sampleId, start: record.start, end: record.end };
  };
  const melodic = MELODIC_SLOTS.map((slot) => clipOf(state.sounds[melodicSoundId(slot)], `Sound ${slot}`));
  const drums = DRUM_SLOTS.map((slot) => {
    const ids = drumSoundIds(slot);
    const slices = ids.map((id, k) => clipOf(state.sounds[id], `Sound ${slot} key ${k + 1}`));
    return slices.some((s) => s) ? { slices } : null;
  });
  return {
    project: {
      tempo: readTempo(state.globals[1]),
      swing: readSwing(state.globals[1]),
      chain: readChain(state.globals[1]),
      melodic,
      drums,
      patterns: state.patterns.map((p) => p.slice()),
    },
    samples,
  };
}

export function emptyProject(tempo = 120): Project {
  return {
    tempo,
    swing: 0,
    chain: [1],
    melodic: new Array(8).fill(null),
    drums: new Array(8).fill(null),
    patterns: Array.from({ length: 16 }, () => {
      const p = new Uint8Array(1032);
      p.fill(0xff, 1024);
      return p;
    }),
  };
}
