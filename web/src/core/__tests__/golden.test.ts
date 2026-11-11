/**
 * Hardware-pinned tests. Each golden fixture is a session whose restore the device
 * accepted exactly; the TypeScript must reproduce the packets, the label streams and the
 * byte-identical restore WAV, and parse the state back without loss.
 */

import { createHash } from 'node:crypto';
import { describe, expect, it } from 'vitest';

import { base64ToBytes, concatBytes } from '../bytes';
import { readChain, readSwing, readTempo } from '../globals';
import { FRAME_START_BYTE, labelsForBody, preambleBytes } from '../labels';
import { encodeRestoreWav } from '../modem/encode';
import { type Packet, decodeFrame, encodePackets, packetsEqual } from '../packets';
import { readCell, readEffects } from '../pattern';
import { parseFrame, serializeState } from '../state';
import fxRules from '../__fixtures__/golden-compiled-fx-rules-001.json';
import webTemplate from '../__fixtures__/golden-web-template-001.json';
import { drumKitGolden as drumKit, melodicGolden as melodic, present } from './local-goldens';
import template from '../__fixtures__/template-empty.json';

type Golden = typeof fxRules;
type Decoded = Golden['decoded'];

const GOLDENS: Golden[] = present(melodic, fxRules, drumKit, webTemplate);

const sha256 = (bytes: Uint8Array): string => createHash('sha256').update(bytes).digest('hex');
const packetsOf = (view: { tag: number; payload: string }[]): Packet[] =>
  view.map((p) => ({ tag: p.tag, payload: base64ToBytes(p.payload) }));

function checkDecoded(packets: Packet[], decoded: Decoded): void {
  const body = encodePackets(packets);
  const frame = decodeFrame(concatBytes([preambleBytes(), body]));
  const state = parseFrame(frame);
  expect(readTempo(state.globals[1])).toBe(decoded.tempo);
  expect(readSwing(state.globals[1])).toBe(decoded.swing);
  expect(readChain(state.globals[1])).toEqual(decoded.chain);
  decoded.patterns.forEach((pattern, index) => {
    const data = state.patterns[index];
    expect(sha256(data)).toBe(pattern.sha256);
    expect(readEffects(data)).toEqual(pattern.effects);
    for (let sound = 1; sound <= 16; sound++) {
      const column = (pattern.cells as Record<string, ({ aux: number; primary: number } | null)[]>)[String(sound)];
      for (let step = 1; step <= 16; step++) {
        const cell = readCell(data, step, sound);
        const expected = column?.[step - 1] ?? null;
        if (!expected) {
          expect(cell).toBeNull();
          continue;
        }
        expect(cell).not.toBeNull();
        const key = expected.aux === 0 ? null : (expected.aux & 0xf) + 1;
        expect(cell!.key).toBe(key);
        const value = expected.primary;
        expect(cell!.pitch).toBe(value & 31);
        expect(cell!.volume).toBe((value >> 6) & 63);
        expect(cell!.filter).toBe((value >> 12) & 63);
        expect(cell!.resonance).toBe((value >> 18) & 63);
      }
    }
  });
  decoded.sounds.forEach((sound) => {
    const record = state.sounds[sound.id];
    if (!sound.record) {
      expect(record).toBeNull();
      return;
    }
    expect(record).not.toBeNull();
    expect(record!.start).toBe(sound.record.start);
    expect(record!.end).toBe(sound.record.end);
    expect(record!.owner).toBe(sound.record.owner);
    expect(record!.codes.length).toBe(sound.record.codes);
    expect(sha256(record!.codes)).toBe(sound.record.codes_sha256);
  });
  // The canonical layout reproduces the device's packets exactly.
  expect(packetsEqual(serializeState(state), packets)).toBe(true);
}

describe('template (empty device backup)', () => {
  it('parses and re-serialises exactly', () => {
    const packets = packetsOf(template.packets);
    expect(sha256(encodePackets(packets))).toBe(template.encoded_body_sha256);
    checkDecoded(packets, template.decoded);
  });
});

describe.each(GOLDENS.map((g) => [g.experiment, g] as const))('%s', (_name, golden) => {
  const packets = packetsOf(golden.frame.packets);
  const body = encodePackets(packets);

  it('encodes the packets to the verified body', () => {
    expect(sha256(body)).toBe(golden.frame.encoded_body_sha256);
    expect(sha256(preambleBytes())).toBe(golden.frame.preamble_sha256);
    const frame = decodeFrame(concatBytes([preambleBytes(), body]));
    expect(frame.endByte).toBe(golden.frame.end_byte);
    expect(packetsEqual(frame.packets, packets)).toBe(true);
    expect(FRAME_START_BYTE + body.length).toBe(golden.frame.end_byte);
  });

  it('builds the label streams the device accepted', () => {
    const streams = labelsForBody(body);
    expect(streams.left.length).toBe(golden.restore.labels.left.count);
    expect(streams.right.length).toBe(golden.restore.labels.right.count);
    expect(sha256(streams.left)).toBe(golden.restore.labels.left.sha256);
    expect(sha256(streams.right)).toBe(golden.restore.labels.right.sha256);
  });

  it('synthesises the byte-identical restore WAV', () => {
    const wav = encodeRestoreWav(labelsForBody(body));
    expect(wav.length).toBe(44 + 4 * golden.restore.frames);
    expect(sha256(wav)).toBe(golden.restore.sha256);
  });

  it('parses the state and decodes every field', () => {
    checkDecoded(packets, golden.decoded);
  });
});
