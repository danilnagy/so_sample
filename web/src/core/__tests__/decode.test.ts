/**
 * Decoder tests. The software round trip always runs. The capture tests read the
 * device recordings from the research folder (12 GB, outside git) and are skipped when
 * they are not present.
 */

import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { base64ToBytes } from '../bytes';
import { labelsForBody } from '../labels';
import { recoverFrame } from '../modem/decode';
import { encodeRestoreWav } from '../modem/encode';
import { type Packet, encodePackets, packetsEqual } from '../packets';
import { parseWav } from '../wav';
import fxRules from '../__fixtures__/golden-compiled-fx-rules-001.json';
import webTemplate from '../__fixtures__/golden-web-template-001.json';
import { drumKitGolden as drumKit, melodicGolden as melodic, present } from './local-goldens';

const ROOT = resolve(__dirname, '../../../..');
const GOLDENS = present(melodic, fxRules, drumKit, webTemplate);
const packetsOf = (view: { tag: number; payload: string }[]): Packet[] =>
  view.map((p) => ({ tag: p.tag, payload: base64ToBytes(p.payload) }));

describe('software round trip', () => {
  it('decodes its own restore back to the same packets', () => {
    const packets = packetsOf(fxRules.frame.packets);
    const wav = parseWav(encodeRestoreWav(labelsForBody(encodePackets(packets))));
    const recovered = recoverFrame(wav, 0.02);
    expect(recovered.attempts[0]).toEqual({ method: 'crossing', passed: true });
    expect(packetsEqual(recovered.frame.packets, packets)).toBe(true);
  });
});

describe('noise before the transfer', () => {
  // A browser recording of a genuine backup failed on 2026-11-07 at the first packet: the
  // input was not silent before the transfer, so the first crossing was not the preamble.
  const packets = packetsOf(fxRules.frame.packets);
  const clean = parseWav(encodeRestoreWav(labelsForBody(encodePackets(packets))));
  const rate = clean.sampleRate;
  let seed = 7;
  const noise = (): number => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return (seed / 2 ** 32) * 2 - 1;
  };
  /** The clean restore with `seconds` of generated audio in front of it on both channels. */
  const withLead = (seconds: number, make: (i: number) => number) => {
    const lead = Math.round(seconds * rate);
    const channels = clean.channels.map((c) => {
      const out = new Float64Array(lead + c.length);
      for (let i = 0; i < lead; i++) out[i] = make(i);
      out.set(c, lead);
      return out;
    });
    return { ...clean, channels };
  };
  const expectRecovered = (wav: typeof clean, viaPreamble: boolean) => {
    const { frame, attempts } = recoverFrame(wav, 0.02);
    expect(packetsEqual(frame.packets, packets)).toBe(true);
    const last = attempts[attempts.length - 1];
    expect(last.passed).toBe(true);
    if (viaPreamble) expect(last.method).toMatch(/^preamble found after \d+ left and \d+ right labels$/);
    else expect(last.method).toBe('crossing');
  };

  it('ignores hiss below the threshold', () => {
    expectRecovered(withLead(1, () => 0.01 * noise()), false);
  });

  it('finds the preamble past hiss above the threshold', () => {
    expectRecovered(withLead(1, () => 0.05 * noise()), true);
  });

  it('finds the preamble past mains hum', () => {
    expectRecovered(withLead(1, (i) => 0.03 * Math.sin((2 * Math.PI * 60 * i) / rate)), true);
  });

  it('discards a click followed by over a second of silence', () => {
    const click = Math.round(0.02 * rate);
    expectRecovered(withLead(1.5, (i) => (i < click ? 0.3 * noise() : 0)), false);
  });

  it('reports when the preamble is in neither channel', () => {
    const junk = withLead(1, () => 0.05 * noise());
    junk.channels = junk.channels.map((c) => c.subarray(0, Math.round(0.9 * rate)));
    expect(() => recoverFrame(junk, 0.02)).toThrow(/preamble search: Preamble not found/);
  });
});

describe('device captures', () => {
  for (const golden of GOLDENS) {
    const path = resolve(ROOT, golden.capture.path);
    const run = existsSync(path) ? it : it.skip;
    run(`${golden.experiment}: decodes the recording to the verified packets`, () => {
      const wav = parseWav(new Uint8Array(readFileSync(path)));
      expect(wav.sampleRate).toBe(golden.capture.sample_rate_hz);
      expect(wav.channels[0].length).toBe(golden.capture.frames);
      const recovered = recoverFrame(wav, golden.capture.decoder_threshold);
      expect(packetsEqual(recovered.frame.packets, packetsOf(golden.frame.packets))).toBe(true);
    });
  }
});
