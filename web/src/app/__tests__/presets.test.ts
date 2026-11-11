// @vitest-environment jsdom
import 'fake-indexeddb/auto';

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';

import { db } from '../db';
import { PRESETS, PRESET_KITS, presetUrl } from '../presets';

/**
 * The projects the app comes with are added whenever the library lacks one: on the first
 * launch all ten, afterwards only what was deleted. The bundled zips are served here by a
 * stubbed fetch that reads them from src/presets.
 */
describe('the bundled projects', () => {
  let requests = 0;
  beforeAll(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        requests++;
        const file = decodeURIComponent(url.split('/').pop() ?? '').replace(/-[A-Za-z0-9_-]{8}(\.sosample|\.kit)\.zip$/, '$1.zip');
        const bytes = readFileSync(join(process.cwd(), 'src/presets', file));
        return new Response(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer, { status: 200 });
      }),
    );
  });
  afterAll(() => vi.unstubAllGlobals());

  it('ships seven kits and ten projects, each with a bundled asset', () => {
    expect(PRESET_KITS.map((k) => k.name)).toEqual(['Synth 505', 'Synth 606', 'Synth 626', 'Synth 707', 'Synth 808', 'Synth 808 Percussion', 'Synth 909']);
    expect(PRESETS).toHaveLength(10);
    expect(PRESETS.map((p) => p.name)).toEqual(['Rainy Rhodes', 'Night Walk', 'Corner Store', 'Dusty Crates', 'Warehouse Jack', 'Motor City', 'Late Shift', 'Rinse Out', 'Echo Chamber', 'Concrete']);
    for (const p of PRESETS) expect(presetUrl(p)).toMatch(/\.sosample\.zip$/);
    for (const k of PRESET_KITS) expect(presetUrl(k)).toMatch(/\.kit\.zip$/);
  });

  it('adds the kits and all ten projects on a first launch, opens the first, and brings back a deleted one on the next launch', async () => {
    const { store } = await import('../store');
    await store.init();
    expect(store.state.projects).toHaveLength(10);
    expect(store.state.kits.map((k) => k.name)).toEqual(['Synth 505', 'Synth 606', 'Synth 626', 'Synth 707', 'Synth 808', 'Synth 808 Percussion', 'Synth 909']);
    expect(store.state.project?.name).toBe('Rainy Rhodes');
    // A first visit shows the welcome instead of the notice; once dismissed it stays away.
    expect(store.state.welcome).toBe(true);
    expect(store.state.notice).toBeNull();
    store.dismissWelcome();
    await new Promise((r) => setTimeout(r, 0));
    const all = await db.projects.toArray();
    expect(new Set(all.map((p) => p.preset))).toEqual(new Set(PRESETS.map((p) => p.slug)));
    // The drums are the standard kits: every hit is one library sample, in its machine's folder, shared by the kits and the projects.
    const folders = new Set(store.state.samples.map((s) => s.folder));
    expect([...folders].sort()).toEqual(['Bass', 'Keys', 'Leads', 'Pads', 'Stabs', 'Synth 505', 'Synth 606', 'Synth 626', 'Synth 707', 'Synth 808', 'Synth 909']);
    const hits = store.state.samples.filter((s) => s.folder.startsWith('Synth '));
    expect(hits.length).toBe(new Set(hits.map((s) => s.name)).size);
    expect(hits.length).toBeLessThanOrEqual(7 * 16);
    const kitSampleIds = new Set(store.state.kits.flatMap((k) => k.slices.filter(Boolean).map((c) => c!.sampleId)));
    for (const p of all) for (const d of p.drums) for (const c of d?.slices ?? []) if (c) expect(kitSampleIds.has(c.sampleId)).toBe(true);
    // A second launch adds nothing and fetches nothing.
    const before = requests;
    await store.init();
    expect(store.state.projects).toHaveLength(10);
    expect(requests).toBe(before);
    // A renamed project still counts as present; a deleted one is added again, named as shipped, reusing the library's samples.
    const motor = all.find((p) => p.preset === 'motor-city')!;
    await store.openProject(motor.id);
    store.renameProject('My Detroit');
    await store.deleteProject(all.find((p) => p.preset === 'concrete')!.id);
    expect(store.state.projects).toHaveLength(9);
    const samplesBefore = store.state.samples.length;
    await store.init();
    expect(store.state.projects).toHaveLength(10);
    expect(store.state.samples).toHaveLength(samplesBefore);
    expect(store.state.projects.map((p) => p.name)).toContain('My Detroit');
    expect(store.state.projects.filter((p) => p.name === 'Concrete')).toHaveLength(1);
    expect(store.state.notice).toMatch(/Added 1 project the app comes with/);
    // Every project still resolves every sample it uses.
    const resolve = store.resolver();
    for (const p of await db.projects.toArray()) for (const c of [...p.melodic, ...p.drums.flatMap((d) => d?.slices ?? [])]) if (c) expect(() => resolve(c.sampleId)).not.toThrow();
    // A deleted kit comes back too.
    await store.deleteKit(store.state.kits.find((k) => k.preset === 'tr-909')!.id);
    await store.init();
    expect(store.state.kits).toHaveLength(7);
    // A copy is the user's own: it carries no preset identity, so deleting the original still brings the original back.
    await store.duplicateProject(motor.id);
    const copy = (await db.projects.toArray()).find((p) => p.name === 'My Detroit copy')!;
    expect(copy.preset).toBeUndefined();
  }, 60000);
});
