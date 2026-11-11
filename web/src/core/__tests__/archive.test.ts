import { describe, expect, it } from 'vitest';

import { base64ToBytes, concatBytes } from '../bytes';
import { preambleBytes } from '../labels';
import { type Packet, decodeFrame, encodePackets } from '../packets';
import { parseFrame } from '../state';
import { emptyPattern, writeCell, writeEffects } from '../pattern';
import { type ArchiveProject, type ArchiveSample, codeFromG711, g711FromCode, mulawCodesFromWav, mulawWav, packKit, packProject, patternFromJson, patternToJson, unpackKit, unpackProject } from '../archive';
import { decodeMulaw } from '../mulaw';
import fxRules from '../__fixtures__/golden-compiled-fx-rules-001.json';
import webTemplate from '../__fixtures__/golden-web-template-001.json';
import { drumKitGolden as drumKit, melodicGolden as melodic, present } from './local-goldens';

const GOLDENS = present(melodic, fxRules, drumKit, webTemplate);
const packetsOf = (view: { tag: number; payload: string }[]): Packet[] => view.map((p) => ({ tag: p.tag, payload: base64ToBytes(p.payload) }));
const text = (bytes: Uint8Array) => new TextDecoder().decode(bytes);

const codes = (length: number, seed: number) => Uint8Array.from({ length }, (_, i) => (i * seed + 11) & 0xff);
const samples: ArchiveSample[] = [
  { id: 'a', name: 'kick', folder: 'drums', codes: codes(3000, 7), sourceName: 'kick.wav', sourceRate: 44100 },
  { id: 'b', name: 'kick', folder: '', codes: codes(5000, 13), sourceName: 'kick (2).wav', sourceRate: 48000, mods: { start: 100, end: 4000, gainDb: -3, normalize: true, fadeIn: 50, fadeOut: 0, compressor: { thresholdDb: -12, ratio: 4, makeupDb: 2 } } },
  { id: 'c', name: 'a/b: "pad"?', folder: 'keys', codes: codes(9000, 3), sourceName: 'pad.aif', sourceRate: 22050 },
  { id: 'unused', name: 'spare', folder: '', codes: codes(500, 5), sourceName: 'spare', sourceRate: 23437.5 },
];

function project(): ArchiveProject {
  const patterns = Array.from({ length: 16 }, () => emptyPattern());
  writeCell(patterns[0], 1, 9, { key: 1, pitch: 0, volume: 0, filter: 0, resonance: 0 });
  writeCell(patterns[0], 5, 1, { key: 5, pitch: 15, volume: 40, filter: 0, resonance: 0 });
  writeCell(patterns[0], 6, 1, { key: null, pitch: 0, volume: 20, filter: 0, resonance: 0 });
  writeEffects(patterns[0], [null, null, 3, ...new Array(13).fill(null)]);
  writeCell(patterns[15], 16, 16, { key: 16, pitch: 25, volume: 63, filter: 63, resonance: 63, bit5: 1 });
  const slices = new Array(16).fill(null);
  slices[0] = { sampleId: 'a', start: 0, end: 3000 };
  slices[1] = { sampleId: 'b', start: 100, end: 3900 };
  slices[15] = { sampleId: 'a', start: 2000, end: 2000 };
  return {
    name: 'My beat',
    tempo: 128,
    swing: 9,
    chain: [1, 1, 16],
    melodic: [{ sampleId: 'c', start: 0, end: 9000 }, null, null, { sampleId: 'c', start: 10, end: 8000 }, null, null, null, null],
    drums: [{ slices }, null, null, null, null, null, null, null],
    patterns,
    kitNames: ['House', null, null, null, null, null, null, 'Named but empty'],
  };
}

describe('pattern JSON', () => {
  it('round-trips every pattern of the hardware goldens to its 1032 bytes', () => {
    for (const golden of GOLDENS) {
      const state = parseFrame(decodeFrame(concatBytes([preambleBytes(), encodePackets(packetsOf(golden.frame.packets))])));
      state.patterns.forEach((data, i) => {
        const json = patternToJson(data);
        expect(Array.from(patternFromJson(json, `Pattern ${i + 1}`))).toEqual(Array.from(data));
      });
    }
  });

  it('writes locks without notes, unlocked parameters left out', () => {
    const json = patternToJson(project().patterns[0]);
    expect(json.effects[2]).toBe(3);
    expect(json.notes).toEqual([
      { step: 1, sound: 9, key: 1 },
      { step: 5, sound: 1, key: 5, pitch: 15, volume: 40 },
      { step: 6, sound: 1, key: null, volume: 20 },
    ]);
  });

  it('refuses notes out of range', () => {
    expect(() => patternFromJson({ effects: new Array(16).fill(null), notes: [{ step: 17, sound: 1, key: 1 }] }, 'Pattern 1')).toThrow(/step must be an integer 1\.\.16/);
    expect(() => patternFromJson({ effects: new Array(16).fill(null), notes: [{ step: 1, sound: 1, key: 1, pitch: 26 }] }, 'Pattern 1')).toThrow(/pitch/);
    expect(() => patternFromJson({ effects: new Array(15).fill(null), notes: [] }, 'Pattern 2')).toThrow(/Pattern 2: sixteen step effects/);
  });
});

/** G.711 decoding as a standard player does it: complement the byte, then sign, exponent and mantissa. */
function g711Level(byte: number): number {
  const inverted = byte ^ 255;
  const magnitude = ((((inverted & 15) << 3) + 132) << ((inverted >> 4) & 7)) - 132;
  return (inverted & 128 ? -magnitude : magnitude) / 32768;
}

describe('mu-law WAV', () => {
  it('writes G.711 bytes that standard players decode to the device levels', () => {
    for (let code = 0; code < 256; code++) {
      const byte = g711FromCode(code);
      expect(codeFromG711(byte)).toBe(code);
      expect(g711Level(byte)).toBeCloseTo(decodeMulaw(code), 12);
    }
  });

  it('round-trips the codes and reads back as mono 8-bit mu-law', () => {
    const original = codes(1001, 9);
    const wav = mulawWav(original);
    expect(text(wav.subarray(0, 4))).toBe('RIFF');
    expect(new DataView(wav.buffer).getUint16(20, true)).toBe(7);
    expect(new DataView(wav.buffer).getUint32(24, true)).toBe(23438);
    expect(wav.length % 2).toBe(0);
    expect(Array.from(mulawCodesFromWav(wav))).toEqual(Array.from(original));
    expect(() => mulawCodesFromWav(wav.subarray(0, 20))).toThrow(/truncated/);
    expect(() => mulawCodesFromWav(wav.subarray(0, 50))).toThrow(/data chunk/);
  });
});

describe('project archives', () => {
  it('packs the referenced samples and a readable project.json, and unpacks the same project', async () => {
    const files = await packProject(project(), samples);
    expect([...files.keys()].sort()).toEqual(['project.json', 'samples/a b pad.wav', 'samples/kick 2.wav', 'samples/kick.wav']);
    const json = JSON.parse(text(files.get('project.json')!));
    expect(json.format).toBe('sosample-project');
    expect(json.sampleRate).toBe(23437.5);
    expect(json.samples.map((s: { file: string; codes: number }) => [s.file, s.codes])).toEqual([
      ['samples/kick.wav', 3000],
      ['samples/kick 2.wav', 5000],
      ['samples/a b pad.wav', 9000],
    ]);
    expect(json.samples[0].edits).toBeUndefined();
    expect(json.samples[1].edits.compressor.ratio).toBe(4);
    expect(json.sounds['1']).toEqual({ sample: 'samples/a b pad.wav', start: 0, end: 9000 });
    expect(json.sounds['9'].name).toBe('House');
    expect(json.sounds['9'].keys['16']).toEqual({ sample: 'samples/kick.wav', start: 2000, end: 2000 });
    expect(json.sounds['16']).toEqual({ name: 'Named but empty' });
    expect(json.sounds['10']).toBeUndefined();
    // Notes and effects sit on one line each.
    expect(text(files.get('project.json')!)).toMatch(/\n {8}\{ "step": 5, "sound": 1, "key": 5, "pitch": 15, "volume": 40 \},\n/);
    expect(text(files.get('project.json')!)).toMatch(/"effects": \[null, null, 3, null/);

    const { project: back, samples: unpacked } = await unpackProject(files);
    expect(unpacked.map((s) => [s.file, s.name, s.folder, s.sourceName, s.sourceRate])).toEqual([
      ['samples/kick.wav', 'kick', 'drums', 'kick.wav', 44100],
      ['samples/kick 2.wav', 'kick', '', 'kick (2).wav', 48000],
      ['samples/a b pad.wav', 'a/b: "pad"?', 'keys', 'pad.aif', 22050],
    ]);
    expect(Array.from(unpacked[1].codes)).toEqual(Array.from(samples[1].codes));
    expect(unpacked[1].mods).toEqual(samples[1].mods);
    expect(unpacked[0].mods).toBeUndefined();
    expect(back.name).toBe('My beat');
    expect([back.tempo, back.swing, back.chain]).toEqual([128, 9, [1, 1, 16]]);
    expect(back.melodic[3]).toEqual({ sampleId: 'samples/a b pad.wav', start: 10, end: 8000 });
    expect(back.drums[0]!.slices[1]).toEqual({ sampleId: 'samples/kick 2.wav', start: 100, end: 3900 });
    expect(back.drums[0]!.slices[15]).toEqual({ sampleId: 'samples/kick.wav', start: 2000, end: 2000 });
    expect(back.drums[1]).toBeNull();
    expect(back.kitNames).toEqual(['House', null, null, null, null, null, null, 'Named but empty']);
    back.patterns.forEach((p, i) => expect(Array.from(p)).toEqual(Array.from(project().patterns[i])));
  });

  it('refuses a missing sample, tampered audio, a malformed window and a newer version', async () => {
    const files = await packProject(project(), samples);
    const edited = async (change: (json: Record<string, unknown>) => void, more?: (f: Map<string, Uint8Array>) => void) => {
      const copy = new Map(files);
      const json = JSON.parse(text(copy.get('project.json')!));
      change(json);
      copy.set('project.json', new TextEncoder().encode(JSON.stringify(json)));
      more?.(copy);
      return unpackProject(copy);
    };
    await expect(edited(() => {}, (f) => f.delete('samples/kick.wav'))).rejects.toThrow(/samples\/kick.wav is missing/);
    await expect(
      edited(
        () => {},
        (f) => {
          const wav = f.get('samples/kick.wav')!.slice();
          wav[100] ^= 1;
          f.set('samples/kick.wav', wav);
        },
      ),
    ).rejects.toThrow(/does not match its checksum/);
    await expect(edited((j) => ((j.sounds as Record<string, { start: number }>)['1'].start = -1))).rejects.toThrow(/Sound 1: window -1\.\.9000 is not a range/);
    // Past the end is kept, as device data holds such windows.
    expect((await edited((j) => ((j.sounds as Record<string, { end: number }>)['1'].end = 9001))).project.melodic[0]!.end).toBe(9001);
    await expect(edited((j) => (j.version = 2))).rejects.toThrow(/newer than this app/);
    await expect(edited((j) => (j.format = 'other'))).rejects.toThrow(/not a sosample-project file/);
    await expect(edited((j) => (j.tempo = 0))).rejects.toThrow(/tempo must be 60\.\.240/);
    await expect(edited((j) => (j.swing = 50))).rejects.toThrow(/swing must be 0\.\.18/);
    expect((await edited((j) => delete j.swing)).project.swing).toBe(0);
    await expect(edited((j) => ((j.patterns as unknown[]).length = 15))).rejects.toThrow(/Sixteen patterns/);
    // Malformed entries are refused with a message, not a raw TypeError, and a chain the device cannot hold is refused at once.
    await expect(edited((j) => ((j.patterns as unknown[])[3] = null))).rejects.toThrow(/Pattern 4: a pattern object is required/);
    await expect(edited((j) => ((j.samples as unknown[])[0] = null))).rejects.toThrow(/Each sample entry must be an object/);
    await expect(edited((j) => (j.chain = new Array(129).fill(1)))).rejects.toThrow(/at most 128/);
    expect((await edited((j) => (j.chain = new Array(128).fill(2)))).project.chain.length).toBe(128);
    // The edits keep to the sample editor's ranges: a compressor ratio under 1 would turn the audio into NaN.
    const kick = (j: Record<string, unknown>) => (j.samples as { edits: Record<string, unknown> }[])[1].edits;
    await expect(edited((j) => ((kick(j).compressor as Record<string, number>).ratio = 0))).rejects.toThrow(/compressor ratio must be 1\.\.20/);
    await expect(edited((j) => (kick(j).gainDb = 40))).rejects.toThrow(/gainDb must be -24\.\.24/);
    await expect(edited((j) => (kick(j).fadeIn = -1))).rejects.toThrow(/fadeIn must be 0\.\.5000/);
  });

  it('refuses a clip of a sample that is not in the library', async () => {
    await expect(packProject({ ...project(), melodic: [{ sampleId: 'gone', start: 0, end: 1 }, null, null, null, null, null, null, null] }, samples)).rejects.toThrow(/Sample gone is not in the library/);
  });
});

describe('kit archives', () => {
  it('round-trips a kit with its samples', async () => {
    const slices = project().drums[0]!.slices;
    const files = await packKit({ name: 'House', slices }, samples);
    expect([...files.keys()].sort()).toEqual(['kit.json', 'samples/kick 2.wav', 'samples/kick.wav']);
    const json = JSON.parse(text(files.get('kit.json')!));
    expect(json.format).toBe('sosample-kit');
    expect(Object.keys(json.keys)).toEqual(['1', '2', '16']);
    const { kit, samples: unpacked } = await unpackKit(files);
    expect(kit.name).toBe('House');
    expect(kit.slices[1]).toEqual({ sampleId: 'samples/kick 2.wav', start: 100, end: 3900 });
    expect(kit.slices.filter(Boolean).length).toBe(3);
    expect(unpacked.length).toBe(2);
    await expect(unpackProject(files)).rejects.toThrow(/no project.json/);
  });
});
