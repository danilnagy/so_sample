/**
 * CRC-additive whitened packets.
 *
 * A packet is tag (u16 LE), payload length (u8), payload, CRC state (u16 LE). Every raw
 * byte is sent as raw + (state & 255) and then fed to the CRC, whose state starts at
 * 0x1d0f for the frame and carries across packets. The frame begins with an empty
 * 0x985b packet and ends with an empty 0x826f packet.
 */

import { bytesEqual } from './bytes';
import { CRC_INITIAL_STATE, crcUpdate } from './crc';
import { FRAME_START_BYTE, type LabelStreams, wireBytes } from './labels';

export const TAG = {
  START: 0x985b,
  END: 0x826f,
  GLOBAL: 0x7d5c,
  SOUND_SELECT: 0x68b5,
  SOUND_DATA: 0xef78,
  PATTERN_SELECT: 0xa041,
  PATTERN_DATA: 0xc498,
} as const;

export interface Packet {
  tag: number;
  payload: Uint8Array;
}

export interface Frame {
  packets: Packet[];
  /** Wire byte index just past the final marker. */
  endByte: number;
  encodedBody: Uint8Array;
}

export function packet(tag: number, payload: Uint8Array | number[] = []): Packet {
  return { tag, payload: payload instanceof Uint8Array ? payload : Uint8Array.from(payload) };
}

export function packetsEqual(a: Packet[], b: Packet[]): boolean {
  return a.length === b.length && a.every((p, i) => p.tag === b[i].tag && bytesEqual(p.payload, b[i].payload));
}

export function decodeFrame(wire: Uint8Array, start = FRAME_START_BYTE): Frame {
  if (!(start >= 0 && start < wire.length)) throw new Error('Frame start is outside the wire bytes');
  let pos = start;
  let state = CRC_INITIAL_STATE;
  const take = (count: number): Uint8Array => {
    if (pos + count > wire.length) throw new Error(`Truncated packet at wire byte ${pos}`);
    const out = new Uint8Array(count);
    for (let i = 0; i < count; i++) {
      const raw = (wire[pos + i] - (state & 255)) & 255;
      state = crcUpdate(state, raw);
      out[i] = raw;
    }
    pos += count;
    return out;
  };
  const packets: Packet[] = [];
  while (pos < wire.length) {
    const begin = pos;
    const header = take(3);
    const tag = header[0] | (header[1] << 8);
    const payload = take(header[2]);
    const expected = state;
    const trailer = take(2);
    if ((trailer[0] | (trailer[1] << 8)) !== expected) {
      throw new Error(`Packet checksum differs at wire byte ${begin}, tag 0x${tag.toString(16)}`);
    }
    if (!packets.length && (tag !== TAG.START || payload.length)) {
      throw new Error('Expected the empty start marker packet');
    }
    packets.push({ tag, payload });
    if (tag === TAG.END) {
      if (payload.length) throw new Error('Final marker has an unexpected payload');
      return { packets, endByte: pos, encodedBody: wire.slice(start, pos) };
    }
  }
  throw new Error('No final marker');
}

export function encodePackets(packets: Packet[]): Uint8Array {
  if (
    !packets.length ||
    packets[0].tag !== TAG.START ||
    packets[0].payload.length ||
    packets[packets.length - 1].tag !== TAG.END ||
    packets[packets.length - 1].payload.length ||
    packets.slice(0, -1).some((p) => p.tag === TAG.END)
  ) {
    throw new Error('Start and final markers are required, with a single final packet');
  }
  let total = 0;
  for (const p of packets) total += 5 + p.payload.length;
  const out = new Uint8Array(total);
  let pos = 0;
  let state = CRC_INITIAL_STATE;
  const emit = (raw: number): void => {
    out[pos++] = (raw + (state & 255)) & 255;
    state = crcUpdate(state, raw);
  };
  for (const p of packets) {
    if (!Number.isInteger(p.tag) || p.tag < 0 || p.tag > 0xffff) throw new Error('Packet tag must fit 16 bits');
    if (p.payload.length > 255) throw new Error('Packet payload must be at most 255 bytes');
    emit(p.tag & 255);
    emit(p.tag >> 8);
    emit(p.payload.length);
    for (const raw of p.payload) emit(raw);
    const trailer = state;
    emit(trailer & 255);
    emit(trailer >> 8);
  }
  return out;
}

export function decodeLabels(streams: LabelStreams): Frame {
  return decodeFrame(wireBytes(streams));
}
