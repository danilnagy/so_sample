/**
 * Shared by the browser-transfer test's build and check (docs/browser-transfer-control.md):
 * compile a project archive exactly as the app does before Send, read packets back into a
 * device state, and compare two states audibly.
 */

import { unzipSync } from 'fflate';

import { unpackProject } from '../src/core/archive';
import { base64ToBytes, concatBytes } from '../src/core/bytes';
import { applyModifications, modifiedLength } from '../src/core/edits';
import { readChain, readSwing, readTempo } from '../src/core/globals';
import { preambleBytes } from '../src/core/labels';
import { type Packet, decodeFrame, encodePackets } from '../src/core/packets';
import { type Clip, type Project, compileProject } from '../src/core/project';
import { type DeviceState, parseFrame, usedPages } from '../src/core/state';
import { emptyTemplateState } from '../src/core/template';

/**
 * An archive compiled as the app's Send compiles it (store.buildLabels): each sample with its
 * edits applied, every clip window fitted inside its sample (Store.fitted), the empty-device
 * template, and the compiler's default layout (kit sharing on).
 */
export async function compileArchive(zip: Uint8Array): Promise<{ name: string; state: DeviceState }> {
  const files = new Map(Object.entries(unzipSync(zip)));
  const { project, samples } = await unpackProject(files);
  const byId = new Map(samples.map((s) => [s.file, s]));
  const resolve = (id: string): Uint8Array => {
    const s = byId.get(id);
    if (!s) throw new Error(`No sample ${id}`);
    return s.mods ? applyModifications(s.codes, s.mods) : s.codes;
  };
  const fit = (clip: Clip | null): Clip | null => {
    if (!clip) return null;
    const s = byId.get(clip.sampleId);
    if (!s) return null;
    const length = modifiedLength(s.mods, s.codes.length);
    if (length <= 0) return null;
    const end = Math.min(clip.end, length);
    return { ...clip, start: Math.min(clip.start, end), end };
  };
  const fitted: Project = {
    tempo: project.tempo,
    swing: project.swing,
    chain: project.chain,
    melodic: project.melodic.map(fit),
    drums: project.drums.map((d) => {
      if (!d) return null;
      const slices = d.slices.map(fit);
      return slices.some(Boolean) ? { slices } : null;
    }),
    patterns: project.patterns,
  };
  return { name: project.name, state: compileProject(fitted, resolve, emptyTemplateState()) };
}

/** A device state from a sosample.packets view. */
export function stateOfPackets(view: { tag: number; payload: string }[]): DeviceState {
  const packets: Packet[] = view.map((p) => ({ tag: p.tag, payload: base64ToBytes(p.payload) }));
  return parseFrame(decodeFrame(concatBytes([preambleBytes(), encodePackets(packets)])));
}

const equalBytes = (a: Uint8Array, b: Uint8Array) => a.length === b.length && a.every((v, i) => v === b[i]);

/**
 * Whether `actual` plays as `target` does, as the core's import-then-compile tests define it:
 * every sound has the same owner and the same codes in its window, every pattern is byte for
 * byte the same, and the chain, tempo and swing agree; and `actual` needs no more pages.
 */
export function audibleChecks(actual: DeviceState, target: DeviceState): Record<string, boolean> {
  const window = (state: DeviceState, id: number): Uint8Array | null => {
    const record = state.sounds[id];
    if (!record) return null;
    const owner = state.sounds[record.owner];
    return owner ? owner.codes.subarray(record.start, record.end) : null;
  };
  let sounds = true;
  for (let id = 0; id < Math.max(actual.sounds.length, target.sounds.length); id++) {
    const a = actual.sounds[id] ?? null;
    const b = target.sounds[id] ?? null;
    if (!a || !b) {
      if (a !== b) sounds = false;
      continue;
    }
    const wa = window(actual, id);
    const wb = window(target, id);
    if (a.owner !== b.owner || !wa || !wb || !equalBytes(wa, wb)) sounds = false;
  }
  return {
    every_sound_plays_the_same_codes: sounds,
    patterns_identical: actual.patterns.length === target.patterns.length && actual.patterns.every((p, i) => equalBytes(p, target.patterns[i])),
    chain_identical: JSON.stringify(readChain(actual.globals[1])) === JSON.stringify(readChain(target.globals[1])),
    tempo_identical: readTempo(actual.globals[1]) === readTempo(target.globals[1]),
    swing_identical: readSwing(actual.globals[1]) === readSwing(target.globals[1]),
    no_more_pages: usedPages(actual) <= usedPages(target),
  };
}
