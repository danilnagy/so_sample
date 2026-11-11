// @vitest-environment jsdom
import 'fake-indexeddb/auto';

import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { beforeAll, describe, expect, it } from 'vitest';

import { readCell } from '../../core/pattern';
import { parseWav } from '../../core/wav';
import { db } from '../db';
import { store } from '../store';
import golden from '../../core/__fixtures__/golden-web-template-001.json';

const ROOT = resolve(__dirname, '../../../..');

describe('backup import', () => {
  beforeAll(async () => {
    await store.init();
  });

  it('round-trips a project through the restore WAV and the decoder', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'tone', name: 'tone', folder: '', codes: Uint8Array.from({ length: 4000 }, (_, i) => (i * 13) & 0x7f), sourceName: 'tone.wav', sourceRate: 44100, createdAt: now, updatedAt: now });
    await store.init();
    store.setTempo(133);
    store.setSwing(3);
    store.setChain([2, 1]);
    store.setMelodic(1, { sampleId: 'tone', start: 0, end: 4000 });
    store.setMelodic(4, { sampleId: 'tone', start: 500, end: 2500 });
    store.setDrumSlice(12, 3, { sampleId: 'tone', start: 0, end: 1000 });
    store.setCell(5, 1, { key: 9, pitch: 13, volume: 36, filter: 63, resonance: 1 });
    store.setCell(1, 12, { key: 3, pitch: 13, volume: 30, filter: 63, resonance: 1 });
    const wav = parseWav(store.buildRestore());
    const before = store.state.project!;
    const summary = await store.importBackup(wav, 'round trip');
    expect(summary).toContain('1 sample');
    const after = store.state.project!;
    expect(after.id).not.toBe(before.id);
    expect(after.tempo).toBe(133);
    expect(after.swing).toBe(3);
    expect(after.chain).toEqual([2, 1]);
    expect(after.melodic[3]).toMatchObject({ start: 500, end: 2500 });
    expect(after.melodic[0]!.sampleId).toBe(after.melodic[3]!.sampleId);
    expect(after.drums[3]!.slices[2]).toMatchObject({ start: 0, end: 1000, sampleId: after.melodic[0]!.sampleId });
    expect(readCell(after.patterns[0], 5, 1)).toMatchObject({ key: 9 });
    expect(readCell(after.patterns[0], 1, 12)).toMatchObject({ key: 3, volume: 30 });
    const sample = store.state.samples.find((s) => s.id === after.melodic[0]!.sampleId)!;
    expect(sample.codes.length).toBe(4000);
    expect(sample.folder).toBe('round trip');
  });

  const capture = resolve(ROOT, golden.capture.path);
  (existsSync(capture) ? it : it.skip)('imports a device recording', async () => {
    const wav = parseWav(new Uint8Array(readFileSync(capture)));
    const summary = await store.importBackup(wav, 'web template');
    // Three buffers: the tone, the Sound 9 kit (kick and snare in one), the chirp.
    expect(summary).toContain('3 samples');
    const project = store.state.project!;
    expect(project.tempo).toBe(100);
    expect(project.chain).toEqual([1, 2]);
    expect(project.drums[0]!.slices[3]).toBeNull();
    expect(project.drums[0]!.slices[4]!.sampleId).toBe(project.melodic[0]!.sampleId);
  });
});
