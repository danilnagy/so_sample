/** Zip packing for project and kit archives. The files inside are stored, not compressed: mu-law audio barely shrinks. */

import { unzipSync, zipSync } from 'fflate';

import type { ArchiveFiles } from '../core/archive';

export function zipFiles(files: ArchiveFiles): Uint8Array {
  const input: Record<string, Uint8Array> = {};
  // Bytes from another realm (a test DOM's TextEncoder, say) are re-wrapped, or fflate would take them for a folder.
  for (const [path, bytes] of files) {
    const view = bytes as ArrayBufferView;
    input[path] = bytes instanceof Uint8Array ? bytes : new Uint8Array(view.buffer, view.byteOffset, view.byteLength);
  }
  return zipSync(input, { level: 0 });
}

/** The files of a zip. A zip of one folder (as a re-zipped export is) reads as if its contents were at the root. */
export function unzipFiles(bytes: Uint8Array): ArchiveFiles {
  let entries: Record<string, Uint8Array>;
  try {
    entries = unzipSync(bytes);
  } catch (error) {
    throw new Error(`Not a zip file: ${(error as Error).message}`);
  }
  const files: ArchiveFiles = new Map();
  for (const [path, data] of Object.entries(entries)) if (!path.endsWith('/') && !path.includes('__MACOSX/')) files.set(path, data);
  if (!files.has('project.json') && !files.has('kit.json')) {
    const nested = [...files.keys()].find((p) => /^[^/]+\/(project|kit)\.json$/.test(p));
    if (nested) {
      const prefix = nested.slice(0, nested.indexOf('/') + 1);
      return new Map([...files].filter(([p]) => p.startsWith(prefix)).map(([p, d]) => [p.slice(prefix.length), d]));
    }
  }
  return files;
}

export async function bytesOf(source: Uint8Array | Blob): Promise<Uint8Array> {
  return source instanceof Uint8Array ? source : new Uint8Array(await source.arrayBuffer());
}
