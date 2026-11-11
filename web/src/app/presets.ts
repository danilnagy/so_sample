/**
 * The seven standard kits and ten projects the app comes with. Built by
 * scripts/build-presets.ts into src/presets, where Vite bundles the zips as hashed assets;
 * the manifest lists them in order. When the app loads it adds any of them the library
 * lacks, so every user has all of them, as ordinary local kits and projects, and one that
 * was deleted comes back on the next load. The projects' drums are the standard kits, so
 * the samples are shared: one library sample per hit, in a folder named after its machine.
 */

import manifest from '@presets/index.json';

export interface Preset {
  /** The stable identity a project record keeps, so the project counts as present however it is renamed. */
  slug: string;
  name: string;
  file: string;
  style: string;
  tempo: number;
  swing: number;
  bars: number;
  pages: number;
  bytes: number;
}

export interface PresetKit {
  slug: string;
  name: string;
  file: string;
  keys: number;
  bytes: number;
}

export const PRESETS: Preset[] = manifest.packs;
export const PRESET_KITS: PresetKit[] = manifest.kits;

/** The zips as bundled asset URLs, by their file name. */
const urls = import.meta.glob('@presets/*.zip', { query: '?url', import: 'default', eager: true }) as Record<string, string>;

export function presetUrl(preset: { name: string; file: string }): string {
  const key = Object.keys(urls).find((k) => k.endsWith(`/${preset.file}`));
  if (!key) throw new Error(`"${preset.name}" is not bundled`);
  return urls[key];
}

export async function fetchPreset(preset: { name: string; file: string; bytes: number }): Promise<Uint8Array> {
  const response = await fetch(presetUrl(preset));
  if (!response.ok) throw new Error(`"${preset.name}" could not be loaded (${response.status})`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (preset.bytes && bytes.length !== preset.bytes) throw new Error(`"${preset.name}" arrived incomplete`);
  return bytes;
}

/** The bundled projects are not added when the page is opened with ?nopresets, for tests and demos that want an empty library. */
export function presetsDisabled(): boolean {
  return typeof location !== 'undefined' && new URLSearchParams(location.search).has('nopresets');
}
