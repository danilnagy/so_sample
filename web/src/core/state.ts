/**
 * The device state as a plain object, and its canonical packet layout.
 *
 * A backup holds, in this order: the start marker, two 255-byte global records, the 16
 * patterns (selector, then 1032 bytes in 255-byte chunks), the 136 sound records
 * (selector, then an optional record), and the final marker. A sound record is a 9-byte
 * header (start u32, end u32, owner u8) followed, when the sound owns a buffer, by its
 * mu-law codes in 4096-code pages; the first page is chunked together with the header
 * (4105 bytes in 255-byte chunks), later pages separately. A 9-byte record whose owner
 * is another sound is a reference into that sound's buffer.
 */

import { bytesEqual, readU32LE, writeU32LE } from './bytes';
import { type Frame, type Packet, TAG, packet } from './packets';

export const GLOBAL_RECORDS = 2;
export const GLOBAL_BYTES = 255;
export const PATTERN_COUNT = 16;
export const PATTERN_BYTES = 1032;
export const SOUND_IDS = 136;
export const PAGE = 4096;
export const CHUNK = 255;

export interface SoundRecord {
  start: number;
  end: number;
  owner: number;
  /** Mu-law codes when this sound owns the buffer (a whole number of pages); else empty. */
  codes: Uint8Array;
}

export interface DeviceState {
  globals: Uint8Array[];
  patterns: Uint8Array[];
  sounds: (SoundRecord | null)[];
}

export function parseFrame(frame: Frame): DeviceState {
  const packets = frame.packets;
  let i = 0;
  const expect = (condition: boolean, message: string): void => {
    if (!condition) throw new Error(`Unsupported backup layout: ${message} (packet ${i})`);
  };
  expect(packets[i]?.tag === TAG.START, 'missing start marker');
  i++;
  const globals: Uint8Array[] = [];
  while (packets[i]?.tag === TAG.GLOBAL) globals.push(packets[i++].payload);
  expect(globals.length === GLOBAL_RECORDS && globals.every((g) => g.length === GLOBAL_BYTES), 'global records');
  const patterns: Uint8Array[] = [];
  for (let number = 0; number < PATTERN_COUNT; number++) {
    expect(packets[i]?.tag === TAG.PATTERN_SELECT && packets[i].payload.length === 1 && packets[i].payload[0] === number, `pattern ${number} selector`);
    i++;
    const chunks: Uint8Array[] = [];
    while (packets[i]?.tag === TAG.PATTERN_DATA) chunks.push(packets[i++].payload);
    const data = join(chunks);
    expect(data.length === PATTERN_BYTES, `pattern ${number} length ${data.length}`);
    patterns.push(data);
  }
  const sounds: (SoundRecord | null)[] = [];
  for (let id = 0; id < SOUND_IDS; id++) {
    expect(packets[i]?.tag === TAG.SOUND_SELECT && packets[i].payload.length === 1 && packets[i].payload[0] === id, `sound ${id} selector`);
    i++;
    const chunks: Uint8Array[] = [];
    while (packets[i]?.tag === TAG.SOUND_DATA) chunks.push(packets[i++].payload);
    if (!chunks.length) {
      sounds.push(null);
      continue;
    }
    const data = join(chunks);
    expect(data.length >= 9 && (data.length - 9) % PAGE === 0, `sound ${id} record length ${data.length}`);
    sounds.push({ start: readU32LE(data, 0), end: readU32LE(data, 4), owner: data[8], codes: data.slice(9) });
  }
  expect(packets[i]?.tag === TAG.END && i === packets.length - 1, 'final marker');
  return { globals, patterns, sounds };
}

export function serializeState(state: DeviceState): Packet[] {
  const out: Packet[] = [packet(TAG.START)];
  if (state.globals.length !== GLOBAL_RECORDS) throw new Error('Two global records are required');
  for (const g of state.globals) {
    if (g.length !== GLOBAL_BYTES) throw new Error('Global records are 255 bytes');
    out.push(packet(TAG.GLOBAL, g));
  }
  if (state.patterns.length !== PATTERN_COUNT) throw new Error('Sixteen patterns are required');
  state.patterns.forEach((data, number) => {
    if (data.length !== PATTERN_BYTES) throw new Error(`Pattern ${number + 1} is not ${PATTERN_BYTES} bytes`);
    out.push(packet(TAG.PATTERN_SELECT, [number]));
    for (const chunk of chunks(data)) out.push(packet(TAG.PATTERN_DATA, chunk));
  });
  if (state.sounds.length !== SOUND_IDS) throw new Error(`${SOUND_IDS} sound slots are required`);
  state.sounds.forEach((record, id) => {
    out.push(packet(TAG.SOUND_SELECT, [id]));
    if (!record) return;
    if (record.codes.length % PAGE) throw new Error(`Sound ${id} buffer is not whole pages`);
    const header = new Uint8Array(9);
    writeU32LE(header, 0, record.start);
    writeU32LE(header, 4, record.end);
    header[8] = record.owner;
    if (!record.codes.length) {
      out.push(packet(TAG.SOUND_DATA, header));
      return;
    }
    const first = new Uint8Array(9 + PAGE);
    first.set(header);
    first.set(record.codes.subarray(0, PAGE), 9);
    for (const chunk of chunks(first)) out.push(packet(TAG.SOUND_DATA, chunk));
    for (let offset = PAGE; offset < record.codes.length; offset += PAGE) {
      for (const chunk of chunks(record.codes.subarray(offset, offset + PAGE))) out.push(packet(TAG.SOUND_DATA, chunk));
    }
  });
  out.push(packet(TAG.END));
  return out;
}

export function cloneState(state: DeviceState): DeviceState {
  return {
    globals: state.globals.map((g) => g.slice()),
    patterns: state.patterns.map((p) => p.slice()),
    sounds: state.sounds.map((s) => (s ? { ...s, codes: s.codes.slice() } : null)),
  };
}

export function statesEqual(a: DeviceState, b: DeviceState): boolean {
  return (
    a.globals.length === b.globals.length &&
    a.globals.every((g, i) => bytesEqual(g, b.globals[i])) &&
    a.patterns.every((p, i) => bytesEqual(p, b.patterns[i])) &&
    a.sounds.every((s, i) => {
      const t = b.sounds[i];
      if (!s || !t) return s === t;
      return s.start === t.start && s.end === t.end && s.owner === t.owner && bytesEqual(s.codes, t.codes);
    })
  );
}

/** Pages of sample memory the state occupies on the device (241 available). */
export function usedPages(state: DeviceState): number {
  let codes = 0;
  for (const s of state.sounds) if (s) codes += s.codes.length;
  return codes / PAGE;
}

function join(parts: Uint8Array[]): Uint8Array {
  let total = 0;
  for (const p of parts) total += p.length;
  const out = new Uint8Array(total);
  let offset = 0;
  for (const p of parts) {
    out.set(p, offset);
    offset += p.length;
  }
  return out;
}

function chunks(data: Uint8Array): Uint8Array[] {
  const out: Uint8Array[] = [];
  for (let i = 0; i < data.length; i += CHUNK) out.push(data.subarray(i, Math.min(i + CHUNK, data.length)));
  return out;
}
