import { createHash } from 'node:crypto';
import { describe, expect, it } from 'vitest';

import { base64ToBytes } from '../bytes';
import { readChain } from '../globals';
import { type Packet, decodeFrame, encodePackets } from '../packets';
import { readCell, writeCell, writeEffects } from '../pattern';
import { MIN_WINDOW_CODES, MemoryLimitError, compileProject, drumSoundIds, emptyProject, importProject, memorySummary, projectPages } from '../project';
import { type DeviceState, PAGE, parseFrame, serializeState, statesEqual, usedPages } from '../state';
import { emptyTemplateState } from '../template';
import fxRules from '../__fixtures__/golden-compiled-fx-rules-001.json';
import webTemplate from '../__fixtures__/golden-web-template-001.json';
import { drumKitGolden as drumKit, melodicGolden as melodic } from './local-goldens';
import { concatBytes } from '../bytes';
import { preambleBytes } from '../labels';

const sha256 = (bytes: Uint8Array): string => createHash('sha256').update(bytes).digest('hex');
const stateOf = (view: { tag: number; payload: string }[]): DeviceState => {
  const packets: Packet[] = view.map((p) => ({ tag: p.tag, payload: base64ToBytes(p.payload) }));
  return parseFrame(decodeFrame(concatBytes([preambleBytes(), encodePackets(packets)])));
};
const codes = (length: number, seed: number): Uint8Array => Uint8Array.from({ length }, (_, i) => (i * 7 + seed) & 0xff);

/** The same sounds, windows and audible codes, allowing a different zero tail. */
function audiblyEqual(a: DeviceState, b: DeviceState): boolean {
  const window = (state: DeviceState, id: number): Uint8Array | null => {
    const record = state.sounds[id];
    if (!record) return null;
    const owner = state.sounds[record.owner];
    if (!owner) throw new Error(`sound ${id} references an empty owner`);
    return owner.codes.subarray(record.start, record.end);
  };
  for (let id = 0; id < a.sounds.length; id++) {
    const x = a.sounds[id];
    const y = b.sounds[id];
    if (!x || !y) {
      if (x !== y) return false;
      continue;
    }
    if (x.owner !== y.owner || x.end - x.start !== y.end - y.start) return false;
    if (Buffer.compare(window(a, id)!, window(b, id)!) !== 0) return false;
  }
  return true;
}

describe('template', () => {
  it('is the empty device backup', () => {
    const state = emptyTemplateState();
    expect(state.sounds.every((s) => s === null)).toBe(true);
    expect(usedPages(state)).toBe(0);
    expect(readChain(state.globals[1])).toEqual([1]);
  });
});

describe('import then compile', () => {
  // Two goldens are local only (local-goldens.ts); the cases for them run where they are present.
  it.each(
    (
      [
        ['melodic notes writer', melodic],
        ['fx rules', fxRules],
        ['drum kit pages', drumKit],
        ['web template', webTemplate],
      ] as const
    ).filter((c): c is readonly [string, NonNullable<(typeof c)[1]>] => c[1] !== null),
  )('reproduces the %s session state', (_name, golden) => {
    const original = stateOf(golden.frame.packets);
    const { project, samples } = importProject(original);
    const compiled = compileProject(project, (id) => samples.get(id)!, emptyTemplateState());
    expect(audiblyEqual(compiled, original)).toBe(true);
    expect(usedPages(compiled)).toBeLessThanOrEqual(usedPages(original));
    expect(compiled.patterns.map(sha256)).toEqual(original.patterns.map(sha256));
    // Chain entries past the length are stale bytes the device keeps; only the fields count.
    expect(readChain(compiled.globals[1])).toEqual(readChain(original.globals[1]));
    expect(compiled.globals[1].subarray(128, 131)).toEqual(original.globals[1].subarray(128, 131));
    // Compiling the imported project again changes nothing.
    const again = importProject(compiled);
    const recompiled = compileProject(again.project, (id) => again.samples.get(id)!, emptyTemplateState());
    expect(statesEqual(recompiled, compiled)).toBe(true);
    // And it serialises to a frame that decodes back to the same state.
    const frame = decodeFrame(concatBytes([preambleBytes(), encodePackets(serializeState(compiled))]));
    expect(statesEqual(parseFrame(frame), compiled)).toBe(true);
  });
});

describe('compile layout', () => {
  const library = new Map<string, Uint8Array>([
    ['tone', codes(10000, 1)],
    ['kick', codes(3000, 2)],
    ['snare', codes(2000, 3)],
    ['chirp', codes(8192, 4)],
  ]);
  const resolve = (id: string): Uint8Array => library.get(id)!;

  it('stores a sample shared by melodic tracks once and references it', () => {
    const project = emptyProject(100);
    project.melodic[0] = { sampleId: 'tone', start: 0, end: 10000 };
    project.melodic[1] = { sampleId: 'tone', start: 2000, end: 6000 };
    project.melodic[7] = { sampleId: 'tone', start: 0, end: 500 };
    const state = compileProject(project, resolve, emptyTemplateState());
    expect(state.sounds[0]).toMatchObject({ start: 0, end: 10000, owner: 0 });
    expect(state.sounds[0]!.codes.length).toBe(3 * PAGE);
    expect(state.sounds[1]).toMatchObject({ start: 2000, end: 6000, owner: 0 });
    expect(state.sounds[1]!.codes.length).toBe(0);
    expect(state.sounds[7]).toMatchObject({ start: 0, end: 500, owner: 0 });
    expect(usedPages(state)).toBe(3);
  });

  it('builds a kit buffer under key 1 and lets slices reference melodic buffers', () => {
    const project = emptyProject(100);
    project.melodic[0] = { sampleId: 'tone', start: 0, end: 10000 };
    const slices: (typeof project.drums)[number] = { slices: new Array(16).fill(null) };
    slices.slices[0] = { sampleId: 'kick', start: 0, end: 3000 };
    slices.slices[1] = { sampleId: 'snare', start: 0, end: 2000 };
    slices.slices[2] = { sampleId: 'kick', start: 500, end: 1500 };
    slices.slices[4] = { sampleId: 'tone', start: 0, end: 4000 };
    project.drums[0] = slices;
    const state = compileProject(project, resolve, emptyTemplateState());
    const ids = drumSoundIds(9);
    expect(state.sounds[ids[0]]).toMatchObject({ start: 0, end: 3000, owner: ids[0] });
    expect(state.sounds[ids[0]]!.codes.length).toBe(2 * PAGE);
    expect(state.sounds[ids[1]]).toMatchObject({ start: 3000, end: 5000, owner: ids[0] });
    expect(state.sounds[ids[2]]).toMatchObject({ start: 500, end: 1500, owner: ids[0] });
    expect(state.sounds[ids[3]]).toBeNull();
    expect(state.sounds[ids[4]]).toMatchObject({ start: 0, end: 4000, owner: 0 });
    expect(state.sounds[ids[0]]!.codes.subarray(3000, 5000)).toEqual(library.get('snare'));
    expect(usedPages(state)).toBe(5);
    // Back through import: the same windows and codes.
    const { project: imported, samples } = importProject(state);
    const recompiled = compileProject(imported, (id) => samples.get(id)!, emptyTemplateState());
    expect(statesEqual(recompiled, state)).toBe(true);
  });

  it('models a sliced sample as sixteen windows into one buffer', () => {
    const project = emptyProject(100);
    const slices = Array.from({ length: 16 }, (_, k) => ({ sampleId: 'chirp', start: 512 * k, end: 512 * k + 512 }));
    slices[1] = { sampleId: 'chirp', start: 256, end: 1500 };
    project.drums[1] = { slices };
    const state = compileProject(project, resolve, emptyTemplateState());
    const ids = drumSoundIds(10);
    expect(state.sounds[ids[0]]!.codes.length).toBe(2 * PAGE);
    expect(state.sounds[ids[1]]).toMatchObject({ start: 256, end: 1500, owner: ids[0] });
    expect(state.sounds[ids[15]]).toMatchObject({ start: 7680, end: 8192, owner: ids[0] });
    expect(usedPages(state)).toBe(2);
  });

  it('refuses a project beyond 241 pages and reports the need', () => {
    const big = new Map<string, Uint8Array>();
    for (let i = 0; i < 8; i++) big.set(`s${i}`, new Uint8Array(31 * PAGE));
    const project = emptyProject(100);
    for (let i = 0; i < 8; i++) project.melodic[i] = { sampleId: `s${i}`, start: 0, end: 31 * PAGE };
    expect(projectPages(project, (id) => big.get(id)!)).toBe(248);
    expect(() => compileProject(project, (id) => big.get(id)!, emptyTemplateState())).toThrow(MemoryLimitError);
    project.melodic[7] = null;
    expect(usedPages(compileProject(project, (id) => big.get(id)!, emptyTemplateState()))).toBe(217);
  });

  it('rejects windows outside the sample or too short', () => {
    const project = emptyProject(100);
    project.melodic[0] = { sampleId: 'tone', start: 0, end: 10001 };
    expect(() => compileProject(project, resolve, emptyTemplateState())).toThrow(/outside/);
    project.melodic[0] = { sampleId: 'tone', start: 200, end: 100 };
    expect(() => compileProject(project, resolve, emptyTemplateState())).toThrow(/window 200\.\.100 ends before it starts/);
  });

  it('writes patterns and globals from the model', () => {
    const project = emptyProject(137);
    project.swing = 6;
    project.chain = [1, 2, 1];
    writeCell(project.patterns[0], 1, 1, { key: 1, pitch: 13, volume: 36, filter: 63, resonance: 1 });
    writeCell(project.patterns[0], 2, 1, { key: null, pitch: 0, volume: 20, filter: 0, resonance: 0 });
    writeCell(project.patterns[1], 5, 9, { key: 3, pitch: 13, volume: 36, filter: 63, resonance: 1 });
    writeEffects(project.patterns[1], [null, null, null, null, 1, 1, null, null, null, null, null, null, null, null, null, 15]);
    project.melodic[0] = { sampleId: 'tone', start: 0, end: 10000 };
    const state = compileProject(project, resolve, emptyTemplateState());
    expect(state.globals[1][129]).toBe(137);
    expect(state.globals[1][130]).toBe(6);
    expect(readChain(state.globals[1])).toEqual([1, 2, 1]);
    expect(readCell(state.patterns[0], 1, 1)).toMatchObject({ key: 1, volume: 36 });
    expect(readCell(state.patterns[0], 2, 1)).toMatchObject({ key: null, volume: 20 });
    expect(state.patterns[0][768]).toBe(0xf0);
    expect(state.patterns[1][768 + 16 * 4 + 8]).toBe(0x12);
    expect(state.patterns[1][1026]).toBe(0x00);
    expect(state.patterns[1][1031]).toBe(0xfe);
  });

  it('keeps windows as short as the device makes them, empty ones included', () => {
    // The factory kits in a device backup (2026-11-07) hold 81-code slices on keys 13 to 16.
    const library = new Map([['hat', Uint8Array.from({ length: 4000 }, (_, i) => (i * 7) & 0x7f)]]);
    const resolve = (id: string) => library.get(id)!;
    const project = emptyProject(120);
    const slices = { slices: new Array(16).fill(null) };
    slices.slices[0] = { sampleId: 'hat', start: 0, end: 4000 };
    slices.slices[12] = { sampleId: 'hat', start: 3919, end: 4000 };
    slices.slices[13] = { sampleId: 'hat', start: 0, end: 12 };
    project.drums[5] = slices;
    const state = compileProject(project, resolve, emptyTemplateState());
    const ids = drumSoundIds(14);
    expect(state.sounds[ids[12]]).toMatchObject({ start: 3919, end: 4000 });
    expect(state.sounds[ids[13]]).toMatchObject({ start: 0, end: 12 });
    const { project: imported, samples } = importProject(state);
    expect(imported.drums[5]!.slices[12]).toMatchObject({ start: 3919, end: 4000 });
    expect(statesEqual(compileProject(imported, (id) => samples.get(id)!, emptyTemplateState()), state)).toBe(true);
    // A device backup (2026-11-07) held an empty window at the end of a kit's buffer.
    slices.slices[14] = { sampleId: 'hat', start: 4000, end: 4000 };
    const withEmpty = compileProject(project, resolve, emptyTemplateState());
    expect(withEmpty.sounds[ids[14]]).toMatchObject({ start: 4000, end: 4000 });
    const reimported = importProject(withEmpty);
    expect(reimported.project.drums[5]!.slices[14]).toMatchObject({ start: 4000, end: 4000 });
    expect(statesEqual(compileProject(reimported.project, (id) => reimported.samples.get(id)!, emptyTemplateState()), withEmpty)).toBe(true);
    slices.slices[14] = { sampleId: 'hat', start: 600, end: 500 + MIN_WINDOW_CODES - 1 };
    expect(() => compileProject(project, resolve, emptyTemplateState())).toThrow(/Sound 14 key 15: window 600\.\.500 ends before it starts/);
  });

  it('reports one row per buffer the device will hold, with its uses', () => {
    const library = new Map([
      ['tone', new Uint8Array(10000)],
      ['kick', new Uint8Array(6000)],
      ['hat', new Uint8Array(3000)],
    ]);
    const resolve = (id: string) => library.get(id)!;
    const project = emptyProject(120);
    project.melodic[0] = { sampleId: 'tone', start: 0, end: 10000 };
    project.melodic[2] = { sampleId: 'tone', start: 2000, end: 6000 };
    const kit9 = { slices: new Array(16).fill(null) };
    kit9.slices[0] = { sampleId: 'kick', start: 0, end: 4100 };
    kit9.slices[1] = { sampleId: 'kick', start: 100, end: 2000 };
    kit9.slices[2] = { sampleId: 'tone', start: 0, end: 500 };
    kit9.slices[3] = { sampleId: 'hat', start: 0, end: 3000 };
    project.drums[0] = kit9;
    const kit10 = { slices: new Array(16).fill(null) };
    kit10.slices[0] = { sampleId: 'hat', start: 0, end: 1000 };
    project.drums[1] = kit10;
    const { rows } = memorySummary(project, resolve);
    expect(rows).toEqual([
      { sampleId: 'tone', storedIn: 'Sound 1', codes: 10000, pages: 3, usedBy: ['Sound 1', 'Sound 3', 'Sound 9 key 3'], windows: [{ start: 0, end: 10000 }, { start: 2000, end: 6000 }, { start: 0, end: 500 }] },
      { sampleId: 'kick', storedIn: 'Sound 9 kit', codes: 4100, pages: 1.2, usedBy: ['Sound 9 key 1', 'Sound 9 key 2'], windows: [{ start: 0, end: 4100 }, { start: 100, end: 2000 }] },
      // Sound 10's hat is a reference into Sound 9's kit, which stores it whole.
      { sampleId: 'hat', storedIn: 'Sound 9 kit', codes: 3000, pages: 0.8, usedBy: ['Sound 9 key 4', 'Sound 10 key 1'], windows: [{ start: 0, end: 3000 }, { start: 0, end: 1000 }] },
    ]);
    // The kit packs its parts: 4100 + 3000 codes is two pages, not three; Sound 10 stores nothing.
    expect(projectPages(project, resolve)).toBe(3 + 2);
    // Without kit sharing Sound 10 stores its own hat, as before kit-sharing-001.
    expect(projectPages(project, resolve, { shareKitSamples: false })).toBe(3 + 2 + 1);
  });

  describe('kit sharing', () => {
    // A three-hit kit on Sounds 11 and 12, as a project loading one standard kit on two drum sounds does.
    const library = new Map([
      ['kick', codes(5000, 1)],
      ['snare', codes(3000, 2)],
      ['hat', codes(1500, 3)],
      ['clap', codes(2500, 4)],
    ]);
    const resolve = (id: string) => library.get(id)!;
    const kit = () => {
      const k = { slices: new Array(16).fill(null) };
      k.slices[0] = { sampleId: 'kick', start: 0, end: 5000 };
      k.slices[2] = { sampleId: 'snare', start: 0, end: 3000 };
      k.slices[6] = { sampleId: 'hat', start: 0, end: 1500 };
      return k;
    };
    const twoKits = () => {
      const project = emptyProject(120);
      project.drums[2] = kit();
      project.drums[3] = kit();
      return project;
    };

    it('finds a sample in the kit that stores the most of it, not the first kit that stored any', () => {
      const long = new Uint8Array(9000).fill(7);
      const project = emptyProject(120);
      const keyOne = (end: number) => {
        const slices = new Array(16).fill(null);
        slices[0] = { sampleId: 'x', start: 0, end };
        return { slices };
      };
      project.drums[2] = keyOne(1000);
      project.drums[3] = keyOne(9000);
      project.drums[4] = keyOne(8000);
      const state = compileProject(project, () => long, emptyTemplateState(), { shareKitSamples: true });
      // Sound 13 plays from Sound 12's 9000 codes rather than storing 8000 of its own: 1 + 3 pages, not 1 + 3 + 2.
      expect(state.sounds[drumSoundIds(13)[0]]).toMatchObject({ owner: drumSoundIds(12)[0], start: 0, end: 8000 });
      expect(state.sounds[drumSoundIds(13)[0]]!.codes.length).toBe(0);
      expect(usedPages(state)).toBe(4);
    });

    it('refuses a kit whose own windows are all empty, rather than store a buffer of no codes', () => {
      const project = emptyProject(120);
      const slices = new Array(16).fill(null);
      slices[0] = { sampleId: 'x', start: 0, end: 0 };
      project.drums[0] = { slices };
      expect(() => compileProject(project, () => new Uint8Array(500), emptyTemplateState())).toThrow(/Sound 9: the kit's windows are all empty/);
    });

    it('is on by default since kit-sharing-001; turned off, each drum sound stores its own copy', () => {
      expect(projectPages(twoKits(), resolve)).toBe(3);
      const state = compileProject(twoKits(), resolve, emptyTemplateState(), { shareKitSamples: false });
      expect(state.sounds[drumSoundIds(11)[0]]!.codes.length).toBeGreaterThan(0);
      expect(state.sounds[drumSoundIds(12)[0]]!.codes.length).toBeGreaterThan(0);
      expect(projectPages(twoKits(), resolve, { shareKitSamples: false })).toBe(2 * 3);
    });

    it('stores a kit once when two drum sounds load it, the second referencing the first buffer with the same windows', () => {
      const project = twoKits();
      const state = compileProject(project, resolve, emptyTemplateState(), { shareKitSamples: true });
      const first = drumSoundIds(11);
      const second = drumSoundIds(12);
      // 9500 codes in one buffer: three pages, once.
      expect(projectPages(project, resolve, { shareKitSamples: true })).toBe(3);
      expect(usedPages(state)).toBe(3);
      expect(state.sounds[second[0]]).toMatchObject({ owner: first[0], start: 0, end: 5000 });
      expect(state.sounds[second[0]]!.codes.length).toBe(0);
      for (const k of [0, 2, 6]) {
        const a = state.sounds[first[k]]!;
        const b = state.sounds[second[k]]!;
        expect([b.owner, b.start, b.end]).toEqual([a.owner, a.start, a.end]);
      }
      // The memory rows show one buffer per hit, used by both sounds.
      const { rows } = memorySummary(project, resolve, { shareKitSamples: true });
      expect(rows.map((r) => [r.sampleId, r.storedIn, r.usedBy])).toEqual([
        ['kick', 'Sound 11 kit', ['Sound 11 key 1', 'Sound 12 key 1']],
        ['snare', 'Sound 11 kit', ['Sound 11 key 3', 'Sound 12 key 3']],
        ['hat', 'Sound 11 kit', ['Sound 11 key 7', 'Sound 12 key 7']],
      ]);
      // A backup of it imports to the same project shape, and compiles back to the same state.
      const { project: imported, samples } = importProject(state);
      expect(statesEqual(compileProject(imported, (id) => samples.get(id)!, emptyTemplateState(), { shareKitSamples: true }), state)).toBe(true);
      // Compiled without sharing, every key still plays the same codes, from two buffers.
      const unshared = compileProject(imported, (id) => samples.get(id)!, emptyTemplateState(), { shareKitSamples: false });
      const played = (st: DeviceState, id: number) => {
        const r = st.sounds[id]!;
        return Buffer.from(st.sounds[r.owner]!.codes.subarray(r.start, r.end)).toString('hex');
      };
      for (const id of [...first, ...second].filter((id) => state.sounds[id])) expect(played(unshared, id)).toBe(played(state, id));
      expect(unshared.sounds[second[0]]!.owner).toBe(second[0]);
    });

    it('stores what an earlier kit lacks, with key 1 in the later buffer, and a longer window than the earlier kit stored', () => {
      const project = twoKits();
      // Sound 11 stores only 2000 codes of the kick; Sound 12 plays all 5000 and adds a clap on key 6.
      project.drums[2]!.slices[0] = { sampleId: 'kick', start: 0, end: 2000 };
      project.drums[3]!.slices[5] = { sampleId: 'clap', start: 0, end: 2500 };
      const state = compileProject(project, resolve, emptyTemplateState(), { shareKitSamples: true });
      const first = drumSoundIds(11);
      const second = drumSoundIds(12);
      // Sound 12 stores its own buffer: key 1's kick (Sound 11 only stored 2000 codes of it, and key 1 always joins its own buffer) and the clap.
      expect(state.sounds[second[0]]).toMatchObject({ owner: second[0], start: 0, end: 5000 });
      expect(state.sounds[second[5]]).toMatchObject({ owner: second[0], start: 5000, end: 7500 });
      // Its snare and hat reference Sound 11's buffer.
      expect(state.sounds[second[2]]).toMatchObject({ owner: first[0], start: state.sounds[first[2]]!.start, end: state.sounds[first[2]]!.end });
      expect(state.sounds[second[6]]).toMatchObject({ owner: first[0], start: state.sounds[first[6]]!.start });
      const { project: imported, samples } = importProject(state);
      expect(audiblyEqual(compileProject(imported, (id) => samples.get(id)!, emptyTemplateState(), { shareKitSamples: true }), state)).toBe(true);
    });

    it('prefers a melodic owner, as before', () => {
      const project = twoKits();
      project.melodic[0] = { sampleId: 'snare', start: 0, end: 3000 };
      const state = compileProject(project, resolve, emptyTemplateState(), { shareKitSamples: true });
      expect(state.sounds[drumSoundIds(11)[2]]!.owner).toBe(state.sounds[drumSoundIds(12)[2]]!.owner);
      expect(state.sounds[drumSoundIds(12)[2]]).toMatchObject({ start: 0, end: 3000 });
    });
  });
});
