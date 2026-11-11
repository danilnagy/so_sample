// @vitest-environment jsdom
import 'fake-indexeddb/auto';

import { beforeAll, describe, expect, it, vi } from 'vitest';

import { DEFAULT_PARAMETERS, changedParameters, effectiveParameter, emptyPattern, readCell, readEffects, writeCell } from '../../core/pattern';
import { db } from '../db';
import { NOTICE_SECONDS, copyName, kitDisplayName, store, voiceWarning } from '../store';
import { wavFromPcm16 } from '../../core/wav';

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

describe('store', () => {
  beforeAll(async () => {
    await store.init();
  });

  it('starts with one empty project and persists edits', async () => {
    expect(store.state.ready).toBe(true);
    expect(store.state.project?.name).toBe('Untitled');
    store.setTempo(100);
    store.setSwing(4);
    store.toggleNote(1, 1);
    store.toggleNote(5, 9);
    store.setEffects([null, null, null, null, 7, null, null, null, null, null, null, null, null, null, null, null]);
    store.appendToChain(2);
    await wait(400);
    const saved = await db.projects.get(store.state.project!.id);
    expect(saved?.tempo).toBe(100);
    expect(saved?.swing).toBe(4);
    expect(saved?.chain).toEqual([1, 2]);
    expect(readCell(saved!.patterns[0], 1, 1)).toMatchObject({ key: 5, volume: 36 });
    expect(readCell(saved!.patterns[0], 5, 9)).toMatchObject({ key: 1 });
    expect(readEffects(saved!.patterns[0])[4]).toBe(7);
  });

  it("copies a new note's parameters from the sound's last note, on the current key", () => {
    store.setCell(1, 1, { key: 7, pitch: 15, volume: 40, filter: 20, resonance: 9 });
    store.toggleNote(9, 1);
    expect(readCell(store.state.project!.patterns[0], 9, 1)).toMatchObject({ key: 5, pitch: 15, filter: 20 });
    store.toggleNote(9, 1);
    expect(readCell(store.state.project!.patterns[0], 9, 1)).toBeNull();
  });

  it('copies and clears patterns', () => {
    store.copyPattern(1, 3);
    expect(readCell(store.state.project!.patterns[2], 1, 1)).toMatchObject({ key: 7 });
    store.clearPattern(3);
    expect(readCell(store.state.project!.patterns[2], 1, 1)).toBeNull();
  });

  it('keeps samples in the library and budgets memory', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'tone', name: 'tone', folder: '', codes: new Uint8Array(5000), sourceName: 'tone.wav', sourceRate: 44100, createdAt: now, updatedAt: now });
    await db.samples.put({ id: 'hit', name: 'hit', folder: 'drums', codes: new Uint8Array(1000), sourceName: 'hit.wav', sourceRate: 48000, createdAt: now, updatedAt: now });
    // The store lists samples from the database at init; emulate a reload.
    await store.init();
    expect(store.state.samples.map((s) => s.name)).toEqual(['hit', 'tone']);
    store.setMelodic(1, { sampleId: 'tone', start: 0, end: 5000 });
    store.setMelodic(2, { sampleId: 'tone', start: 1000, end: 3000 });
    store.setDrumSlice(9, 1, { sampleId: 'hit', start: 0, end: 1000 });
    store.setDrumSlice(9, 2, { sampleId: 'tone', start: 0, end: 2000 });
    expect(store.pages()).toBe(3);
    store.setDrumSlice(10, 16, { sampleId: 'tone', start: 4680, end: 5000 });
    expect(store.pages()).toBe(3);
    const wav = store.buildRestore();
    expect(wav.length).toBeGreaterThan(44);
    await store.deleteSample('tone');
    expect(store.state.project!.melodic[0]).toBeNull();
    expect(store.state.project!.drums[1]).toBeNull();
    expect(store.state.project!.drums[0]!.slices[1]).toBeNull();
    expect(store.pages()).toBe(1);
  });

  it('shows the project as saved after deleting it with a save pending', async () => {
    const doomed = store.state.project!.id;
    store.toggleNote(1, 9);
    expect(store.state.saving).toBe(true);
    await store.deleteProject(doomed);
    expect(store.state.saving).toBe(false);
    expect(store.state.project!.id).not.toBe(doomed);
  });

  it('exports a project archive and imports it back, reusing samples with the same audio', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'arc', name: 'arc', folder: 'f', codes: Uint8Array.from({ length: 2000 }, (_, i) => i & 0xff), sourceName: 'arc.wav', sourceRate: 44100, createdAt: now, updatedAt: now });
    await store.init();
    store.setMelodic(3, { sampleId: 'arc', start: 10, end: 1500 });
    store.setDrumSlice(12, 2, { sampleId: 'arc', start: 0, end: 2000 });
    store.toggleNote(4, 3);
    store.setKitName(12, 'Arc kit');
    const before = store.state.project!;
    const { name, bytes } = await store.projectArchive();
    expect(name).toMatch(/\.sosample\.zip$/);
    const count = store.state.samples.length;
    const message = await store.importProjectArchive(bytes);
    expect(message).toMatch(/0 samples added, 1 reused/);
    expect(store.state.samples.length).toBe(count);
    const after = store.state.project!;
    expect(after.id).not.toBe(before.id);
    expect(after.name).toBe(before.name);
    expect(after.melodic[2]).toEqual({ sampleId: 'arc', start: 10, end: 1500 });
    expect(after.drums[3]!.slices[1]).toEqual({ sampleId: 'arc', start: 0, end: 2000 });
    expect(after.kitNames?.[3]).toBe('Arc kit');
    expect(Array.from(after.patterns[0])).toEqual(Array.from(before.patterns[0]));
    // Without the sample in the library, the import adds it, name and folder included.
    await store.deleteSample('arc');
    expect(await store.importProjectArchive(bytes)).toMatch(/1 sample added, 0 reused/);
    expect(store.state.samples.some((s) => s.name === 'arc' && s.folder === 'f')).toBe(true);
    expect(store.state.project!.melodic[2]!.start).toBe(10);
    for (const id of [after.id, store.state.project!.id]) await store.deleteProject(id);
    expect(store.state.project!.id).toBe(before.id);
  });

  it('exports a kit archive and imports it as a saved kit loaded into a sound', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'kk', name: 'kk', folder: '', codes: new Uint8Array(3000).fill(7), sourceName: 'kk', sourceRate: 23437.5, createdAt: now, updatedAt: now });
    await store.init();
    store.setDrumSlice(14, 1, { sampleId: 'kk', start: 0, end: 1000 });
    store.setDrumSlice(14, 5, { sampleId: 'kk', start: 1000, end: 3000 });
    store.setKitName(14, 'Exported');
    const saved = await store.saveKit(14, 'Exported');
    const { name, bytes } = await store.kitArchive(saved!.id);
    expect(name).toBe('Exported.kit.zip');
    await store.importKitArchive(bytes, 15);
    expect(store.state.kits.filter((k) => k.name === 'Exported').length).toBe(2);
    expect(store.state.project!.drums[6]!.slices[4]).toEqual({ sampleId: 'kk', start: 1000, end: 3000 });
    expect(store.state.project!.kitNames?.[6]).toBe('Exported');
  });

  it('deletes several samples at once and empties the clips that used them', async () => {
    const now = Date.now();
    for (const id of ['m1', 'm2', 'm3']) {
      await db.samples.put({ id, name: id, folder: 'bulk', codes: new Uint8Array(1000), sourceName: id, sourceRate: 23437.5, createdAt: now, updatedAt: now });
    }
    await store.init();
    store.setMelodic(5, { sampleId: 'm1', start: 0, end: 1000 });
    store.setMelodic(6, { sampleId: 'm3', start: 0, end: 1000 });
    store.setDrumSlice(15, 1, { sampleId: 'm2', start: 0, end: 1000 });
    store.setDrumSlice(15, 2, { sampleId: 'm3', start: 0, end: 1000 });
    store.openSampleEditor('m2');
    await store.deleteSamples(['m1', 'm2']);
    expect(store.state.samples.map((s) => s.id).filter((id) => id.startsWith('m'))).toEqual(['m3']);
    expect(store.state.project!.melodic[4]).toBeNull();
    expect(store.state.project!.melodic[5]).toEqual({ sampleId: 'm3', start: 0, end: 1000 });
    expect(store.state.project!.drums[6]!.slices[0]).toBeNull();
    expect(store.state.project!.drums[6]!.slices[1]).toEqual({ sampleId: 'm3', start: 0, end: 1000 });
    expect(store.state.library.editing).toBeNull();
    expect(await db.samples.get('m1')).toBeUndefined();
    await store.deleteSamples([]);
  });

  it('toggles preview mute and solo per sound and per drum key, and saves them with the project', async () => {
    store.toggleMute(3);
    expect(store.state.project!.mutes[2]).toBe(true);
    // A solo drops the mutes: the two never apply together at one level.
    store.toggleSolo(9);
    store.toggleSliceMute(9, 4);
    store.toggleSliceSolo(16, 16);
    const p = store.state.project!;
    expect(p.mutes[2]).toBe(false);
    expect(p.solos[8]).toBe(true);
    expect(p.sliceMutes![0][3]).toBe(true);
    expect(p.sliceSolos![7][15]).toBe(true);
    expect(p.sliceMutes![1].every((m) => !m)).toBe(true);
    store.toggleSolo(9);
    expect(store.state.project!.solos[8]).toBe(false);
    await wait(400);
    const saved = (await db.projects.get(p.id))!;
    expect(saved.sliceMutes![0][3]).toBe(true);
    expect(saved.sliceSolos![7][15]).toBe(true);
    store.clearMix();
  });

  it('keeps mutes and solos exclusive at each level, and clears them all at once', () => {
    store.toggleMute(1);
    store.toggleMute(2);
    store.toggleSolo(3);
    expect(store.state.project!.mutes.some(Boolean)).toBe(false);
    expect(store.state.project!.solos[2]).toBe(true);
    store.toggleMute(4);
    expect(store.state.project!.solos.some(Boolean)).toBe(false);
    expect(store.state.project!.mutes[3]).toBe(true);
    store.toggleSliceSolo(9, 1);
    store.toggleSliceMute(9, 2);
    expect(store.state.project!.sliceSolos![0].some(Boolean)).toBe(false);
    expect(store.state.project!.sliceMutes![0][1]).toBe(true);
    // Another kit's flags are untouched by the exclusivity of the first.
    store.toggleSliceSolo(10, 5);
    expect(store.state.project!.sliceMutes![0][1]).toBe(true);
    store.clearMix();
    const p = store.state.project!;
    expect(p.mutes.some(Boolean) || p.solos.some(Boolean)).toBe(false);
    expect(p.sliceMutes).toBeUndefined();
    expect(p.sliceSolos).toBeUndefined();
  });

  it("copies and clears a pattern's effects without touching its notes", () => {
    store.selectPattern(1);
    store.setEffects([3, null, null, null, null, 7, ...new Array(10).fill(null)]);
    store.toggleNote(2, 9);
    store.selectPattern(2);
    store.toggleNote(5, 1);
    store.selectPattern(1);
    store.startCopy('fx');
    expect(store.state.copying).toEqual({ kind: 'fx', from: 1 });
    store.copyTo(2);
    expect(store.state.copying).toBeNull();
    expect(store.state.pattern).toBe(2);
    const second = store.state.project!.patterns[1];
    expect(readEffects(second).slice(0, 6)).toEqual([3, null, null, null, null, 7]);
    expect(readCell(second, 5, 1)?.key).toBeTruthy();
    expect(readCell(second, 2, 9)).toBeNull();
    store.clearEffects(2);
    expect(readEffects(store.state.project!.patterns[1]).every((fx) => fx === null)).toBe(true);
    expect(readCell(store.state.project!.patterns[1], 5, 1)?.key).toBeTruthy();
    store.startCopy('pattern');
    store.cancelCopy();
    expect(store.state.copying).toBeNull();
    store.selectPattern(1);
    store.clearPattern(1);
    store.clearPattern(2);
  });

  it('gives a new note the current key, with the parameters of the nearest note before it, else after it, else the defaults', () => {
    store.selectPattern(3);
    // The current key starts at 5 for a melodic sound and 1 for a drum.
    expect(store.currentKey(1)).toBe(5);
    expect(store.currentKey(9)).toBe(1);
    store.toggleNote(5, 1);
    expect(readCell(store.state.project!.patterns[2], 5, 1)).toMatchObject({ key: 5, ...DEFAULT_PARAMETERS });
    store.toggleNote(5, 9);
    expect(readCell(store.state.project!.patterns[2], 5, 9)?.key).toBe(1);
    // A roll click programs key 7 on step 10 and makes 7 the current key; writing a cell directly does not.
    store.setRollNote(10, 1, 7);
    store.setStepParameter(10, 1, 'pitch', 15);
    store.setStepParameter(10, 1, 'volume', 30);
    expect(store.currentKey(1)).toBe(7);
    store.setCell(14, 1, { key: 2, pitch: 13, volume: 36, filter: 63, resonance: 1 });
    expect(store.currentKey(1)).toBe(7);
    // New notes take key 7 everywhere; their parameters come from step 10 before step 12, from step 5 before step 8, and from step 5 (the nearest after) at step 2.
    store.toggleNote(12, 1);
    store.toggleNote(8, 1);
    store.toggleNote(2, 1);
    const data = store.state.project!.patterns[2];
    expect(readCell(data, 12, 1)).toMatchObject({ key: 7, pitch: 15, volume: 30 });
    expect(readCell(data, 8, 1)).toMatchObject({ key: 7, pitch: DEFAULT_PARAMETERS.pitch });
    expect(readCell(data, 2, 1)?.key).toBe(7);
    // Moving a note in the roll makes its key current too; removing one leaves the current key alone.
    store.setRollNote(12, 1, 3);
    expect(readCell(data === store.state.project!.patterns[2] ? data : store.state.project!.patterns[2], 12, 1)).toMatchObject({ key: 3, pitch: 15 });
    expect(store.currentKey(1)).toBe(3);
    store.setRollNote(12, 1, 3);
    expect(store.currentKey(1)).toBe(3);
    // The key is saved with the project, per sound.
    expect(store.state.project!.keys![0]).toBe(3);
    expect(store.state.project!.keys![8]).toBe(1);
    store.clearPattern(3);
    store.selectPattern(1);
    store.setCurrentKey(1, 5);
  });

  it('runs the pad layout: view and sound choices, the current key, and pad taps that add and remove notes', () => {
    expect(store.state.mobile).toEqual({ view: 'sound', sound: 1, step: null });
    store.setMobileView('song');
    store.setMobileSound(9);
    expect(store.state.mobile).toEqual({ view: 'song', sound: 9, step: null });
    // The key strip sets the sound's current key; it stays with the sound when another is chosen.
    store.setCurrentKey(9, 3);
    store.setMobileSound(2);
    expect(store.currentKey(9)).toBe(3);
    expect(store.currentKey(2)).toBe(5);
    store.selectPattern(4);
    // A blank pad takes the current key and becomes the selected step; a note elsewhere is selected first; the selected note goes.
    store.setCurrentKey(2, 7);
    store.tapStep(1, 2);
    store.tapStep(5, 2);
    expect(store.state.mobile.step).toBe(5);
    const data = () => store.state.project!.patterns[3];
    expect(readCell(data(), 1, 2)?.key).toBe(7);
    expect(readCell(data(), 5, 2)?.key).toBe(7);
    store.tapStep(9, 9);
    expect(readCell(data(), 9, 9)?.key).toBe(3);
    expect(store.state.mobile.step).toBe(9);
    store.tapStep(1, 2);
    expect(readCell(data(), 1, 2)?.key).toBe(7);
    expect(store.state.mobile.step).toBe(1);
    store.tapStep(1, 2);
    expect(readCell(data(), 1, 2)).toBeNull();
    // Changing sound drops the selection.
    store.setMobileSound(3);
    expect(store.state.mobile.step).toBeNull();
    store.clearPattern(4);
    store.selectPattern(1);
    store.setMobileView('pattern');
    store.setMobileSound(1);
    store.setCurrentKey(2, 5);
    store.setCurrentKey(9, 1);
  });

  it('removes a step\'s locks, one parameter or all, so it holds the values before it', () => {
    store.selectPattern(5);
    for (const step of [1, 5, 9]) store.toggleNote(step, 1);
    store.setStepParameter(5, 1, 'volume', 20);
    store.setStepParameter(5, 1, 'filter', 40);
    const data = () => store.state.project!.patterns[4];
    // Step 5 changes two values and step 9 changes them back.
    expect(changedParameters(data(), 1).get(5)).toEqual(['volume', 'filter']);
    expect(changedParameters(data(), 1).get(9)).toEqual(['volume', 'filter']);
    // One lock removed: the step holds step 1's volume, so only the filter still changes.
    store.resetStepParameters(5, 1, ['volume']);
    expect(readCell(data(), 5, 1)).toMatchObject({ key: 5, volume: 0, filter: 40 });
    expect(effectiveParameter(data(), 5, 1, 'volume')).toEqual({ code: DEFAULT_PARAMETERS.volume, own: false });
    expect(changedParameters(data(), 1).get(5)).toEqual(['filter']);
    // All of them: the note keeps its key with no locks, and no step changes anything, so the dots go.
    store.resetStepParameters(5, 1);
    expect(readCell(data(), 5, 1)).toMatchObject({ key: 5, pitch: 0, volume: 0, filter: 0, resonance: 0 });
    expect(changedParameters(data(), 1).size).toBe(0);
    // A lock without a note loses the lock and, with nothing left, the cell.
    store.setStepParameter(12, 1, 'pitch', 20);
    store.setStepParameter(12, 1, 'volume', 10);
    store.resetStepParameters(12, 1, ['pitch']);
    expect(readCell(data(), 12, 1)).toMatchObject({ key: null, pitch: 0, volume: 10 });
    store.resetStepParameters(12, 1);
    expect(readCell(data(), 12, 1)).toBeNull();
    store.clearPattern(5);
    store.selectPattern(1);
  });

  it('keeps the locks a step already holds when a note is added to it, from the grid, the roll or the pads', () => {
    store.selectPattern(6);
    // A filter lock set from the parameter row before any note exists on the step.
    store.setStepParameter(3, 1, 'filter', 20);
    store.tapStep(3, 1);
    const data = () => store.state.project!.patterns[5];
    expect(readCell(data(), 3, 1)).toMatchObject({ key: 5, filter: 20, pitch: DEFAULT_PARAMETERS.pitch });
    store.setStepParameter(7, 1, 'volume', 10);
    store.toggleNote(7, 1);
    expect(readCell(data(), 7, 1)).toMatchObject({ key: 5, volume: 10, filter: 20 });
    store.setStepParameter(11, 1, 'pitch', 20);
    store.setRollNote(11, 1, 9);
    expect(readCell(data(), 11, 1)).toMatchObject({ key: 9, pitch: 20, volume: 10 });
    store.clearPattern(6);
    store.selectPattern(1);
    store.setMobileStep(null);
    store.setCurrentKey(1, 5);
  });

  it('selects a song entry and moves or removes it, keeping at least one pattern', () => {
    expect(store.state.playbackMode).toBe('song');
    store.appendToChain(3);
    store.appendToChain(5);
    expect(store.state.project!.chain.slice(-2)).toEqual([3, 5]);
    const last = store.state.project!.chain.length - 1;
    store.selectSongEntry(last);
    expect(store.state.songEntry).toBe(last);
    store.moveSongEntry(1); // already last: nothing
    expect(store.state.project!.chain[last]).toBe(5);
    store.moveSongEntry(-1); // the selection follows the entry
    expect(store.state.project!.chain.slice(-2)).toEqual([5, 3]);
    expect(store.state.songEntry).toBe(last - 1);
    store.removeSongEntry();
    expect(store.state.project!.chain.slice(-1)).toEqual([3]);
    expect(store.state.songEntry).toBeNull();
    // Selecting again deselects; a selection past the end goes with a shorter chain.
    store.selectSongEntry(0);
    store.selectSongEntry(0);
    expect(store.state.songEntry).toBeNull();
    store.selectSongEntry(last - 1);
    store.clearChain();
    expect(store.state.project!.chain).toEqual([1]);
    expect(store.state.songEntry).toBeNull();
    store.selectSongEntry(0);
    store.removeSongEntry(); // the last pattern stays
    expect(store.state.project!.chain).toEqual([1]);
    store.selectSongEntry(null);
  });

  it('clears a notice after a few seconds and caches the voice warning per pattern', async () => {
    // Earlier tests left notices with real timers running; start clean so only this test's timer counts.
    store.notify(null);
    vi.useFakeTimers();
    try {
      store.notify('Imported');
      expect(store.state.notice).toBe('Imported');
      vi.advanceTimersByTime(NOTICE_SECONDS * 1000 - 100);
      expect(store.state.notice).toBe('Imported');
      vi.advanceTimersByTime(200);
      expect(store.state.notice).toBeNull();
      store.notify('One');
      store.notify(null);
      expect(store.state.notice).toBeNull();
    } finally {
      vi.useRealTimers();
    }
    const data = emptyPattern();
    expect(voiceWarning(data)).toBeNull();
    for (const sound of [1, 2, 3, 4, 11]) writeCell(data, 3, sound, { key: 1, pitch: 0, volume: 0, filter: 0, resonance: 0 });
    // The cache is by array identity: the same bytes object keeps its first answer until replaced.
    expect(voiceWarning(data)).toBeNull();
    expect(voiceWarning(data.slice())).toBe('4 voices: step 3 drops sound 4');
  });

  it('switches and deletes projects', async () => {
    const first = store.state.project!.id;
    await store.newProject();
    expect(store.state.project!.id).not.toBe(first);
    expect(store.state.projects.length).toBe(2);
    await store.openProject(first);
    expect(store.state.project!.id).toBe(first);
    await store.deleteProject(first);
    expect(store.state.project!.id).not.toBe(first);
    expect(store.state.projects.length).toBe(1);
  });

  it('duplicates the current project as an independent copy', async () => {
    const original = store.state.project!;
    store.setTempo(97);
    store.setCell(3, 2, { key: 5, pitch: 13, volume: 36, filter: 63, resonance: 1 });
    await store.duplicateProject();
    const copy = store.state.project!;
    expect(copy.id).not.toBe(original.id);
    expect(copy.name).toBe(`${original.name} copy`);
    expect(copy.tempo).toBe(97);
    expect(readCell(copy.patterns[0], 3, 2)).toMatchObject({ key: 5 });
    expect(store.state.projects.map((p) => p.id)).toContain(original.id);
    expect((await db.settings.get('lastProject'))?.value).toBe(copy.id);
    store.setCell(3, 2, null);
    store.setTempo(120);
    await wait(400);
    const saved = await db.projects.get(original.id);
    expect(saved?.tempo).toBe(97);
    expect(readCell(saved!.patterns[0], 3, 2)).toMatchObject({ key: 5 });
    await store.duplicateProject();
    expect(store.state.project!.name).toBe(`${original.name} copy 2`);
    // Any listed project can be duplicated, not only the current one.
    await store.duplicateProject(original.id);
    expect(store.state.project!.name).toBe(`${original.name} copy 3`);
    expect(store.state.project!.tempo).toBe(97);
  });

  it('clears a whole drum kit at once and leaves the pattern notes', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'kit', name: 'kit', folder: '', codes: new Uint8Array(4000), sourceName: 'kit.wav', sourceRate: 44100, createdAt: now, updatedAt: now });
    await store.init();
    for (let key = 1; key <= 16; key++) store.setDrumSlice(11, key, { sampleId: 'kit', start: (key - 1) * 250, end: key * 250 });
    store.toggleNote(1, 11);
    expect(store.state.project!.drums[2]!.slices.filter(Boolean).length).toBe(16);
    store.clearDrumKit(11);
    expect(store.state.project!.drums[2]).toBeNull();
    expect(readCell(store.state.project!.patterns[0], 1, 11)).toMatchObject({ key: 1 });
    await wait(400);
    expect((await db.projects.get(store.state.project!.id))?.drums[2]).toBeNull();
  });

  it('keeps an empty window from the device when a project is reopened', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'buf', name: 'buf', folder: '', codes: new Uint8Array(1000), sourceName: 'buf', sourceRate: 23437.5, createdAt: now, updatedAt: now });
    await store.init();
    store.setDrumSlice(12, 1, { sampleId: 'buf', start: 0, end: 1000 });
    store.setDrumSlice(12, 15, { sampleId: 'buf', start: 1000, end: 1000 });
    store.setDrumSlice(12, 2, { sampleId: 'buf', start: 900, end: 1200 });
    const id = store.state.project!.id;
    await store.newProject();
    await store.openProject(id);
    const slices = store.state.project!.drums[3]!.slices;
    expect(slices[14]).toMatchObject({ start: 1000, end: 1000 });
    // The window past the sample's end is kept as written and fitted only on the way to the device.
    expect(slices[1]).toMatchObject({ start: 900, end: 1200 });
    const fitted = store.fitted(store.state.project!).drums[3]!.slices;
    expect(fitted[14]).toMatchObject({ start: 1000, end: 1000 });
    expect(fitted[1]).toMatchObject({ start: 900, end: 1000 });
    store.clearDrumKit(12);
  });

  it('a trim never rewrites the windows of the sounds that use the sample: dragged back, they play whole again', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'long', name: 'long', folder: '', codes: new Uint8Array(4000).fill(100), sourceName: 'long', sourceRate: 23437.5, createdAt: now, updatedAt: now });
    await store.init();
    store.setClip({ kind: 'melodic', slot: 1 }, { sampleId: 'long', start: 0, end: 4000 });
    const mods = { start: 0, end: 4000, gainDb: 0, normalize: false, fadeIn: 0, fadeOut: 0, compressor: null };
    store.setSampleMods('long', { ...mods, end: 1000 });
    expect(store.state.project!.melodic[0]).toMatchObject({ start: 0, end: 4000 });
    expect(store.fitted(store.state.project!).melodic[0]).toMatchObject({ start: 0, end: 1000 });
    store.setSampleMods('long', mods);
    expect(store.fitted(store.state.project!).melodic[0]).toMatchObject({ start: 0, end: 4000 });
    store.setClip({ kind: 'melodic', slot: 1 }, null);
  });

  it('a project made current any way drops clips of samples deleted while it was closed, and is remembered', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'gone', name: 'gone', folder: '', codes: new Uint8Array(1000), sourceName: 'gone', sourceRate: 23437.5, createdAt: now, updatedAt: now });
    await store.init();
    store.setClip({ kind: 'melodic', slot: 2 }, { sampleId: 'gone', start: 0, end: 1000 });
    const b = store.state.project!.id;
    await store.newProject();
    const a = store.state.project!.id;
    await store.deleteSamples(['gone']);
    // Deleting the open project opens the most recent other one: B, cleaned, and remembered for next time.
    await store.deleteProject(a);
    expect(store.state.project!.id).toBe(b);
    expect(store.state.project!.melodic[1]).toBeNull();
    expect((await db.settings.get('lastProject'))?.value).toBe(b);
    expect(store.pages()).not.toBeNull();
  });

  it('stacks editors: an editor opened from another returns to it on close', () => {
    expect(store.state.editors).toEqual([]);
    store.openKitEditor(10);
    store.openClipEditor({ kind: 'drum', slot: 10, key: 3 });
    expect(store.state.editors.map((e) => e.kind)).toEqual(['kit', 'clip']);
    expect(store.modalOpen()).toBe(true);
    // Editing a sample opens the Library above the stack with that sample expanded; Escape folds the Library first.
    store.openSampleEditor('kit');
    expect(store.state.library).toEqual({ open: true, target: null, editing: 'kit' });
    store.closeSampleEditor();
    expect(store.state.library).toEqual({ open: true, target: null, editing: null });
    store.openSampleEditor('kit');
    store.closeTopLayer();
    expect(store.state.library).toEqual({ open: true, target: null, editing: null });
    store.closeTopLayer();
    expect(store.state.library.open).toBe(false);
    expect(store.state.editors.length).toBe(2);
    // The Library keeps its target when a sample is opened for editing from it, and closes when an editor opens.
    store.openLibrary({ kind: 'drum', slot: 10, key: 3 });
    store.openSampleEditor('kit');
    expect(store.state.library).toEqual({ open: true, target: { kind: 'drum', slot: 10, key: 3 }, editing: 'kit' });
    store.openClipEditor({ kind: 'melodic', slot: 1 });
    expect(store.state.library.open).toBe(false);
    expect(store.state.editors.length).toBe(3);
    store.closeEditor();
    expect(store.state.editors).toEqual([{ kind: 'kit', slot: 10 }, { kind: 'clip', target: { kind: 'drum', slot: 10, key: 3 } }]);
    store.closeTopLayer();
    store.closeTopLayer();
    expect(store.state.editors).toEqual([]);
    expect(store.modalOpen()).toBe(false);
    store.closeTopLayer();
    expect(store.state.editors).toEqual([]);
  });

  it('undo and redo: each edit is a step, back to the pattern it changed; the mix is not a step and is left alone', async () => {
    await store.newProject();
    expect(store.canUndo()).toBe(false);
    // Separate clicks are separate tasks: the updates of one task are one action, so the test waits between them.
    const click = () => Promise.resolve();
    store.selectPattern(3);
    store.toggleNote(1, 1);
    await click();
    store.setTempo(100);
    await click();
    store.toggleMute(2);
    const muted = store.state.project!.mutes;
    expect(store.canUndo()).toBe(true);
    store.undo();
    expect(store.state.project!.tempo).toBe(120);
    store.selectPattern(1);
    store.undo();
    // Back on the pattern the note was on, without it; the mute pressed after both edits stays.
    expect(store.state.pattern).toBe(3);
    expect(readCell(store.state.project!.patterns[2], 1, 1)).toBeNull();
    expect(store.state.project!.mutes).toBe(muted);
    expect(store.canUndo()).toBe(false);
    store.redo();
    store.redo();
    expect(readCell(store.state.project!.patterns[2], 1, 1)?.key).not.toBeNull();
    expect(store.state.project!.tempo).toBe(100);
    expect(store.canRedo()).toBe(false);
    // A new edit drops the redo steps.
    store.undo();
    await click();
    store.setSwing(5);
    expect(store.canRedo()).toBe(false);
  });

  it("undo: a roll click, which writes the note and the sound's current key, is one step; the key stays chosen", async () => {
    await store.newProject();
    await Promise.resolve();
    store.setRollNote(5, 1, 9);
    expect(store.currentKey(1)).toBe(9);
    await Promise.resolve();
    store.undo();
    expect(readCell(store.state.project!.patterns[store.state.pattern - 1], 5, 1)).toBeNull();
    expect(store.canUndo()).toBe(false);
    expect(store.currentKey(1)).toBe(9);
    // Choosing a key alone is no step.
    await Promise.resolve();
    store.setCurrentKey(1, 4);
    expect(store.canUndo()).toBe(false);
  });

  it('undo: edits while one field has the keyboard are one step; another project starts a new history', async () => {
    await store.newProject();
    const field = document.createElement('input');
    document.body.append(field);
    field.focus();
    store.setTempo(1 + 99);
    store.setTempo(101);
    store.setTempo(102);
    field.blur();
    field.remove();
    store.undo();
    expect(store.state.project!.tempo).toBe(120);
    expect(store.canUndo()).toBe(false);
    store.setTempo(90);
    const first = store.state.project!.id;
    await store.newProject();
    expect(store.canUndo()).toBe(false);
    await store.openProject(first);
    expect(store.canUndo()).toBe(false);
  });

  it('editing a note keeps its timing (length or retrigger); a new note does not copy a neighbour\'s', async () => {
    await store.newProject();
    store.selectPattern(1);
    store.setCell(1, 9, { key: 1, ...DEFAULT_PARAMETERS, timing: 4 });
    // A parameter lock and a move to another key are edits of the same note.
    store.setStepParameter(1, 9, 'volume', 50);
    store.setRollNote(1, 9, 3);
    expect(readCell(store.state.project!.patterns[0], 1, 9)).toMatchObject({ key: 3, volume: 50, timing: 4 });
    // A new note takes the neighbour's parameters but the default timing.
    store.toggleNote(2, 9);
    const fresh = readCell(store.state.project!.patterns[0], 2, 9)!;
    expect(fresh.volume).toBe(50);
    expect(fresh.timing).toBeUndefined();
  });

  it('the guide shows editors and dialogs in place: none counts as a modal, and leaving the guide closes them all', () => {
    store.setGuide(true);
    store.openClipEditor({ kind: 'melodic', slot: 1 });
    store.openDevice('send');
    store.openLibrary(null);
    // In the page, not over it: Space and the grid's shortcuts keep working.
    expect(store.modalOpen()).toBe(false);
    store.setGuide(false);
    expect(store.state.editors).toEqual([]);
    expect(store.state.device).toBeNull();
    expect(store.state.library.open).toBe(false);
    expect(store.modalOpen()).toBe(false);
  });

  it('names kits, saves them, and loads them into another drum sound', async () => {
    const now = Date.now();
    await db.samples.put({ id: 'snare', name: 'snare', folder: '', codes: new Uint8Array(3000), sourceName: 'snare.wav', sourceRate: 44100, createdAt: now, updatedAt: now });
    await db.samples.put({ id: 'gone', name: 'gone', folder: '', codes: new Uint8Array(3000), sourceName: 'gone.wav', sourceRate: 44100, createdAt: now, updatedAt: now });
    await store.init();
    store.setDrumSlice(13, 1, { sampleId: 'snare', start: 0, end: 3000 });
    store.setDrumSlice(13, 2, { sampleId: 'snare', start: 100, end: 900 });
    store.setDrumSlice(13, 3, { sampleId: 'gone', start: 0, end: 500 });
    const project = () => store.state.project!;
    expect(kitDisplayName(project(), store.state.samples, 13)).toBe('snare');
    expect(kitDisplayName(project(), store.state.samples, 14)).toBe('Kit 14');
    store.setKitName(13, 'Rim kit');
    expect(kitDisplayName(project(), store.state.samples, 13)).toBe('Rim kit');
    const saved = await store.saveKit(13, 'Rim kit');
    expect(saved?.slices.filter(Boolean).length).toBe(3);
    expect((await db.kits.get(saved!.id))?.name).toBe('Rim kit');
    // Replacing keeps the id; a different name adds a kit.
    store.setDrumSlice(13, 4, { sampleId: 'snare', start: 0, end: 128 });
    await store.saveKit(13, 'Rim kit', saved!.id);
    expect(store.state.kits.filter((k) => k.name === 'Rim kit').length).toBe(1);
    expect((await db.kits.get(saved!.id))?.slices.filter(Boolean).length).toBe(4);
    expect(await store.saveKit(14, 'nothing')).toBeNull();
    // A sample deleted since saving leaves its key empty.
    await store.deleteSample('gone');
    store.loadKit(saved!.id, 15);
    const loaded = project().drums[6]!.slices;
    expect(loaded[0]).toMatchObject({ sampleId: 'snare', start: 0, end: 3000 });
    expect(loaded[1]).toMatchObject({ start: 100, end: 900 });
    expect(loaded[2]).toBeNull();
    expect(loaded[3]).toMatchObject({ end: 128 });
    expect(project().kitNames?.[6]).toBe('Rim kit');
    expect(store.state.notice).toMatch(/1 key left empty/);
    // Clearing forgets the name; duplicating copies names; deleting removes the saved kit.
    store.clearDrumKit(15);
    expect(project().kitNames?.[6]).toBeNull();
    await store.duplicateProject();
    expect(project().kitNames?.[4]).toBe('Rim kit');
    await store.deleteKit(saved!.id);
    expect(store.state.kits.some((k) => k.id === saved!.id)).toBe(false);
    expect(await db.kits.get(saved!.id)).toBeUndefined();
    store.clearDrumKit(13);
  });

  it('imports dropped WAV files onto consecutive pads', async () => {
    const tone = (n: number) => {
      const pcm = new Int16Array(n);
      for (let i = 0; i < n; i++) pcm[i] = Math.round(8000 * Math.sin(i / 5));
      return new File([wavFromPcm16(pcm, 1, 44100) as BlobPart], `tone${n}.wav`, { type: 'audio/wav' });
    };
    await store.assignFilesToPads(16, 15, [tone(4410), tone(8820), tone(2205)]);
    const slices = store.state.project!.drums[7]!.slices;
    expect(slices[14]).toMatchObject({ start: 0 });
    expect(slices[15]).toMatchObject({ start: 0 });
    expect(store.state.samples.find((s) => s.id === slices[14]!.sampleId)?.name).toBe('tone4410');
    expect(store.state.samples.find((s) => s.id === slices[15]!.sampleId)?.name).toBe('tone8820');
    // Only two keys remain from key 15: the third file is not imported.
    expect(store.state.samples.some((s) => s.name === 'tone2205')).toBe(false);
    expect(slices[14]!.end).toBe(store.state.samples.find((s) => s.id === slices[14]!.sampleId)!.codes.length);
    store.clearDrumKit(16);
  });

  it('edits notes from the roll: add, move with parameters, remove, and fill a lock', () => {
    store.selectPattern(5);
    const cell = (step: number, sound: number) => readCell(store.state.project!.patterns[4], step, sound);
    // A new note copies the sound's previous note, with the roll's key.
    store.setCell(1, 3, { key: 2, pitch: 15, volume: 40, filter: 20, resonance: 9 });
    store.setRollNote(5, 3, 13);
    expect(cell(5, 3)).toMatchObject({ key: 13, pitch: 15, volume: 40, filter: 20, resonance: 9 });
    // Another key on the same step moves the note and keeps its parameters.
    store.setCell(5, 3, { key: 13, pitch: 10, volume: 30, filter: 63, resonance: 1 });
    store.setRollNote(5, 3, 7);
    expect(cell(5, 3)).toMatchObject({ key: 7, pitch: 10, volume: 30, filter: 63, resonance: 1 });
    // The key the step already has removes the note.
    store.setRollNote(5, 3, 7);
    expect(cell(5, 3)).toBeNull();
    // A lock without a note becomes a note; its locked values stay, the rest come from the last note.
    store.setCell(9, 3, { key: null, pitch: 0, volume: 50, filter: 0, resonance: 0 });
    store.setRollNote(9, 3, 4);
    expect(cell(9, 3)).toMatchObject({ key: 4, pitch: 15, volume: 50, filter: 20, resonance: 9 });
    // With no note on the sound, defaults apply.
    store.setRollNote(2, 4, 16);
    expect(cell(2, 4)).toMatchObject({ key: 16, pitch: 13, volume: 36, filter: 63, resonance: 1 });
    store.clearPattern(5);
    store.selectPattern(1);
  });

  it('unrolls and rolls up sounds independently', () => {
    store.toggleRoll(9);
    store.toggleRoll(2);
    expect(store.state.unrolled).toEqual([2, 9]);
    store.unroll(9);
    store.unroll(5);
    expect(store.state.unrolled).toEqual([2, 5, 9]);
    store.toggleRoll(5);
    store.toggleRoll(9);
    expect(store.state.unrolled).toEqual([2]);
    store.toggleRoll(2);
    expect(store.state.unrolled).toEqual([]);
  });

  it('renames a folder, merging into an existing one, and deletes a folder keeping its samples', async () => {
    const now = Date.now();
    await db.samples.bulkPut([
      { id: 'f1', name: 'f1', folder: 'Hats', codes: new Uint8Array(300), sourceName: 'f1', sourceRate: 44100, createdAt: now, updatedAt: now },
      { id: 'f2', name: 'f2', folder: 'Hats', codes: new Uint8Array(300), sourceName: 'f2', sourceRate: 44100, createdAt: now, updatedAt: now },
      { id: 'f3', name: 'f3', folder: 'Kicks', codes: new Uint8Array(300), sourceName: 'f3', sourceRate: 44100, createdAt: now, updatedAt: now },
    ]);
    await store.init();
    const folderOf = (id: string) => store.state.samples.find((s) => s.id === id)!.folder;
    await store.renameFolder('Hats', ' Cymbals ');
    expect([folderOf('f1'), folderOf('f2'), folderOf('f3')]).toEqual(['Cymbals', 'Cymbals', 'Kicks']);
    expect((await db.samples.get('f1'))?.folder).toBe('Cymbals');
    await store.renameFolder('Cymbals', 'Kicks');
    expect(store.state.samples.filter((s) => s.folder === 'Kicks').map((s) => s.id).sort()).toEqual(['f1', 'f2', 'f3']);
    await store.renameFolder('Kicks', '   ');
    expect(folderOf('f3')).toBe('Kicks');
    await store.deleteFolder('Kicks');
    expect([folderOf('f1'), folderOf('f2'), folderOf('f3')]).toEqual(['', '', '']);
    expect((await db.samples.get('f3'))?.folder).toBe('');
    expect(store.state.samples.length).toBeGreaterThanOrEqual(3);
    await db.samples.bulkDelete(['f1', 'f2', 'f3']);
    await store.init();
  });

  it('sets a step parameter from the lane, creating and clearing locks without a note', () => {
    store.selectPattern(6);
    const cell = (step: number, sound: number) => readCell(store.state.project!.patterns[5], step, sound);
    store.setStepParameter(3, 2, 'volume', 50);
    expect(cell(3, 2)).toEqual({ key: null, pitch: 0, volume: 50, filter: 0, resonance: 0, bit5: 0 });
    store.setStepParameter(3, 2, 'filter', 20);
    expect(cell(3, 2)).toMatchObject({ key: null, volume: 50, filter: 20 });
    store.setStepParameter(3, 2, 'volume', 0);
    expect(cell(3, 2)).toMatchObject({ volume: 0, filter: 20 });
    store.setStepParameter(3, 2, 'filter', 0);
    expect(cell(3, 2)).toBeNull();
    store.setCell(5, 2, { key: 4, pitch: 13, volume: 36, filter: 63, resonance: 1 });
    store.setStepParameter(5, 2, 'pitch', 20);
    expect(cell(5, 2)).toMatchObject({ key: 4, pitch: 20, volume: 36 });
    store.setStepParameter(5, 2, 'volume', 0);
    expect(cell(5, 2)).toMatchObject({ key: 4, volume: 0 });
    store.setLaneParameter(2, 'filter');
    expect(store.state.laneParameter[2]).toBe('filter');
    store.clearPattern(6);
    store.selectPattern(1);
  });

  it('names copies without stacking the word copy', () => {
    expect(copyName('Beat', [])).toBe('Beat copy');
    expect(copyName('Beat', ['Beat copy'])).toBe('Beat copy 2');
    expect(copyName('Beat copy', ['Beat copy'])).toBe('Beat copy 2');
    expect(copyName('Beat copy 2', ['Beat copy', 'Beat copy 2'])).toBe('Beat copy 3');
  });

  it('remembers the audio input chosen for backups', async () => {
    expect(store.state.inputDevice).toBe('');
    await store.setInputDevice('line-in-id');
    expect(store.state.inputDevice).toBe('line-in-id');
    expect((await db.settings.get('inputDevice'))?.value).toBe('line-in-id');
    await store.setInputDevice('');
  });
});
