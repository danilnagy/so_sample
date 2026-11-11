/**
 * Build the seven standard kits and the ten projects the app comes with, into src/presets,
 * with the manifest the app imports. Vite bundles the zips as hashed assets and the app
 * adds any of them a library lacks when it loads (src/app/presets.ts). The projects' drums
 * are the standard kits, so a hit is one library sample however many use it.
 *
 *   npx tsx scripts/build-presets.ts                                 synthesized drums → src/presets (shipped)
 *   npx tsx scripts/build-presets.ts --pack "<TR pack folder>"       the TR pack's hits → presets-tr (local only)
 *   npx tsx scripts/build-presets.ts [--pack "<folder>"] <output>    either, to a folder of your choice
 *
 * The shipped set is synthesized (scripts/drum-synth.ts) and freely licensed. The TR set
 * uses a third-party pack whose audio may not be redistributed: its output folder is ignored
 * by git, and its zips can be imported into the app by hand (Projects, Import project; the
 * kit editor's import) for local use.
 *
 * Every pack is checked against the device's four voices and 241 pages as it is written.
 */

import { mkdirSync, readdirSync, unlinkSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

import { zipSync } from 'fflate';

import { packKit } from '../src/core/archive';
import { KITS, buildKit } from './kit-tools';
import { cornerStore, dustyCrates, motorCity, warehouseJack } from './make-genre-packs';
import { nightWalk, rainyRhodes } from './make-lofi-packs';
import { concrete, echoChamber, lateShift, rinseOut } from './make-more-packs';
import { type SongSpec, slugOf, writePack } from './pack-tools';

/** The presets in presentation order, with the style each shows off. */
const PRESETS: { spec: () => SongSpec; style: string }[] = [
  { spec: rainyRhodes, style: 'lofi' },
  { spec: nightWalk, style: 'lofi' },
  { spec: cornerStore, style: 'soul boom bap' },
  { spec: dustyCrates, style: 'soul boom bap' },
  { spec: warehouseJack, style: 'Chicago house' },
  { spec: motorCity, style: 'Detroit house' },
  { spec: lateShift, style: 'trap' },
  { spec: rinseOut, style: 'jungle' },
  { spec: echoChamber, style: 'dub' },
  { spec: concrete, style: 'techno' },
];

/** The index format the app reads (src/app/presets.ts). */
export const PRESET_INDEX_VERSION = 1;

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const at = args.indexOf('--pack');
  const pack = at >= 0 ? args[at + 1] : undefined;
  if (at >= 0 && !pack) throw new Error('usage: build-presets.ts [--pack <TR pack folder>] [output folder]');
  const rest = args.filter((_, i) => at < 0 || (i !== at && i !== at + 1));
  const out = rest[0] ?? (pack === undefined ? 'src/presets' : 'presets-tr');
  mkdirSync(out, { recursive: true });
  // Earlier builds' zips go, so the folder holds exactly what the index names.
  for (const stale of readdirSync(out)) if (stale.endsWith('.zip')) unlinkSync(join(out, stale));
  // The standard kits first: the projects' drums are these kits, so their samples are shared.
  const kits = [];
  for (const spec of KITS) {
    const built = buildKit(spec, pack);
    const files = await packKit({ name: built.name, slices: built.slices }, built.samples);
    // The slug is the kit's identity in a user's library, the same for both forms: a library holding one is not sent the other.
    const input: Record<string, Uint8Array> = {};
    for (const [p, b] of files) input[p] = b;
    const bytes = zipSync(input, { level: 6 });
    const file = `${slugOf(spec.name)}.kit.zip`;
    writeFileSync(join(out, file), bytes);
    kits.push({ slug: slugOf(spec.name), name: built.name, file, keys: built.slices.filter(Boolean).length, bytes: bytes.length });
    console.log(`${built.name}: ${built.slices.filter(Boolean).length} keys → ${file}`);
  }
  const packs = [];
  for (const { spec, style } of PRESETS) {
    const facts = await writePack(spec(), pack, out);
    console.log(facts.description);
    packs.push({ slug: facts.slug, name: facts.name, file: facts.file, style, tempo: facts.tempo, swing: facts.swing, bars: facts.bars, pages: facts.pages, bytes: facts.bytes });
  }
  writeFileSync(join(out, 'index.json'), JSON.stringify({ version: PRESET_INDEX_VERSION, kits, packs }, null, 2) + '\n');
  console.log(`${kits.length} kits and ${packs.length} projects, ${((packs.reduce((s, p) => s + p.bytes, 0) + kits.reduce((s, k) => s + k.bytes, 0)) / 1024).toFixed(0)} KB → ${join(out, 'index.json')}`);
}

main().catch((error) => {
  console.error((error as Error).message);
  process.exit(1);
});
