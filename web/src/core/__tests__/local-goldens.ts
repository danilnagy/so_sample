/**
 * Golden device states kept out of the public repository: their research device's starting
 * state carried sample audio of unknown origin (possibly factory content), so they live in
 * __fixtures__/local, which git ignores. With them present the tests check them like the
 * other goldens; without them those cases skip.
 */

import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import type fxRules from '../__fixtures__/golden-compiled-fx-rules-001.json';

export type Golden = typeof fxRules;

const LOCAL = resolve(__dirname, '../__fixtures__/local');

/** A local golden by name, or null when it is not on this machine. */
export function localGolden(name: string): Golden | null {
  const path = resolve(LOCAL, `${name}.json`);
  return existsSync(path) ? (JSON.parse(readFileSync(path, 'utf8')) as Golden) : null;
}

export const melodicGolden = localGolden('golden-compiled-melodic-notes-writer-001');
export const drumKitGolden = localGolden('golden-compiled-drum-kit-pages-001');

/** The goldens present, in the usual order. */
export function present(...goldens: (Golden | null)[]): Golden[] {
  return goldens.filter((g): g is Golden => g !== null);
}
