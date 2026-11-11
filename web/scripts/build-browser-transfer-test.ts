/**
 * Build the target for the registered browser-transfer test (docs/browser-transfer-control.md):
 * the app's own Send and Import, run on the device. Copies the bundled Concrete project
 * archive into experiments/browser-transfer-001 as the project the person imports into the
 * app and sends, and compiles it exactly as the app's Send does into the expected packets.
 * scripts/prepare_browser_transfer_test.py registers the test from these files.
 *
 *   npx tsx scripts/build-browser-transfer-test.ts      (from web/)
 *
 * reference-restore.wav is the same compile encoded as a restore. It is not played to the
 * device (the browser sends); it gives the Python decoder the expected artifact.
 */

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { bytesToBase64 } from '../src/core/bytes';
import { labelsForBody } from '../src/core/labels';
import { encodeRestoreWav } from '../src/core/modem/encode';
import { encodePackets } from '../src/core/packets';
import { serializeState, usedPages } from '../src/core/state';
import { audibleChecks, compileArchive, stateOfPackets } from './browser-transfer-tools';

const OUT = resolve(import.meta.dirname, '../../experiments/browser-transfer-001');
const SOURCE = resolve(import.meta.dirname, '../src/presets/concrete.sosample.zip');

async function main(): Promise<void> {
  const zip = new Uint8Array(readFileSync(SOURCE));
  const { name, state } = await compileArchive(zip);
  const packets = serializeState(state);
  const body = encodePackets(packets);
  const view = packets.map((p) => ({ tag: p.tag, payload: bytesToBase64(p.payload) }));
  // The packets must read back to the same state, or the check could not compare against them.
  const back = stateOfPackets(view);
  if (!Object.values(audibleChecks(back, state)).every(Boolean)) throw new Error('The target packets do not read back to the compiled state');
  const wav = encodeRestoreWav(labelsForBody(body));
  mkdirSync(OUT, { recursive: true });
  writeFileSync(resolve(OUT, 'send-project.sosample.zip'), zip);
  writeFileSync(resolve(OUT, 'reference-restore.wav'), wav);
  writeFileSync(resolve(OUT, 'packets.json'), JSON.stringify({ schema: 'sosample.packets', packets: view }));
  writeFileSync(
    resolve(OUT, 'project.json'),
    JSON.stringify(
      { name, source: 'web/src/presets/concrete.sosample.zip', pages: usedPages(state), packets: packets.length, body_bytes: body.length, transfer_seconds: (wav.length - 44) / 4 / 44100 },
      null,
      1,
    ),
  );
  console.log(JSON.stringify({ name, pages: usedPages(state), packets: packets.length, seconds: (wav.length - 44) / 4 / 44100 }));
}

main().catch((error) => {
  console.error((error as Error).message);
  process.exit(1);
});
