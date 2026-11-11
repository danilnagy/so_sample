/**
 * The browser-transfer test's import check (docs/browser-transfer-control.md): compile the
 * project the app made from its own recording of the device's backup, exported from the app
 * as a project archive, and compare it with the registered target, printing JSON.
 *
 *   npx tsx scripts/check-browser-import.ts <imported.sosample.zip> <packets.json>
 */

import { readFileSync } from 'node:fs';

import { usedPages } from '../src/core/state';
import { audibleChecks, compileArchive, stateOfPackets } from './browser-transfer-tools';

async function main(): Promise<void> {
  const [archive, packets] = process.argv.slice(2);
  if (!archive || !packets) throw new Error('usage: check-browser-import.ts <imported.sosample.zip> <packets.json>');
  const view = JSON.parse(readFileSync(packets, 'utf8'));
  if (view.schema !== 'sosample.packets') throw new Error('Expected a sosample packets file');
  const target = stateOfPackets(view.packets);
  const { name, state } = await compileArchive(new Uint8Array(readFileSync(archive)));
  const checks = audibleChecks(state, target);
  console.log(JSON.stringify({ name, passed: Object.values(checks).every(Boolean), checks, pages: usedPages(state), target_pages: usedPages(target) }));
}

main().catch((error) => {
  console.error((error as Error).message);
  process.exit(1);
});
