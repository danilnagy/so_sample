/**
 * Build importable drum kit archives (<name>.kit.zip) from a folder of one-shot samples.
 *
 *   npx tsx scripts/make-kits.ts ["<pack folder>"] "<output folder>"   (no pack: synthesized kits)
 *
 * The kits and their key layout are defined in kit-tools.ts, shared with the bundled
 * projects, so a project's drums and the kit library hold the same samples.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { basename, join } from 'node:path';

import { zipSync } from 'fflate';

import { packKit } from '../src/core/archive';
import { SAMPLE_RATE } from '../src/core/mulaw';
import { pagesFor } from '../src/core/project';
import { KITS, buildKit, synthName } from './kit-tools';

async function main(): Promise<void> {
  // One argument: synthesized kits into that folder; two: the pack's samples.
  const args = process.argv.slice(2);
  const [pack, out] = args.length >= 2 ? args : [undefined, args[0]];
  if (!out) throw new Error('usage: make-kits.ts [<pack folder>] <output folder>');
  mkdirSync(out, { recursive: true });
  const lines: string[] = [];
  for (const spec of KITS) {
    const { samples, slices, stored } = buildKit(spec, pack);
    const name = pack === undefined ? synthName(spec.name) : spec.name;
    const files = await packKit({ name, slices }, samples);
    const input: Record<string, Uint8Array> = {};
    for (const [p, b] of files) input[p] = b;
    const file = join(out, `${name}.kit.zip`);
    writeFileSync(file, zipSync(input, { level: 0 }));
    lines.push(`${name}: ${slices.filter(Boolean).length} keys, ${(stored / SAMPLE_RATE).toFixed(2)} s stored, ${pagesFor(stored)} pages → ${basename(file)}`);
  }
  console.log(lines.join('\n'));
}

main().catch((error) => {
  console.error((error as Error).message);
  process.exit(1);
});
