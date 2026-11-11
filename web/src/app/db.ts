/** Local storage: IndexedDB through Dexie. Everything the app keeps lives here. */

import Dexie, { type EntityTable } from 'dexie';

import type { Modifications } from '../core/edits';
import type { Clip, DrumTrack } from '../core/project';

export interface SampleRecord {
  id: string;
  name: string;
  folder: string;
  /** Native mu-law codes at 23437.5 Hz, as imported. */
  codes: Uint8Array;
  /** Non-destructive edits applied on export and preview; absent when untouched. */
  mods?: Modifications;
  sourceName: string;
  sourceRate: number;
  createdAt: number;
  updatedAt: number;
}

export interface ProjectRecord {
  id: string;
  name: string;
  tempo: number;
  swing: number;
  chain: number[];
  melodic: (Clip | null)[];
  drums: (DrumTrack | null)[];
  patterns: Uint8Array[];
  /** Preview-only mute and solo per sound 1..16; the device has no such state. */
  mutes: boolean[];
  solos: boolean[];
  /** Preview-only mute and solo per key of each drum sound 9..16; absent in older projects. */
  sliceMutes?: boolean[][];
  sliceSolos?: boolean[][];
  /** App-only names of the drum sounds 9..16; absent in projects saved before kits had names. */
  kitNames?: (string | null)[];
  /** App-only current key per sound 1..16: the key a new note takes and an audition plays; absent in older projects. */
  keys?: number[];
  /** The bundled project this record was added from (its slug), so the app knows it is present; absent on the user's own projects and on copies. */
  preset?: string;
  createdAt: number;
  updatedAt: number;
}

/** A drum kit saved in the app, to load into any drum sound. App-only: the device has no kits. */
export interface KitRecord {
  id: string;
  name: string;
  /** Sixteen slices, key 1 first, into samples of the library. */
  slices: (Clip | null)[];
  /** The bundled kit this record was added from (its slug); absent on the user's own kits. */
  preset?: string;
  createdAt: number;
  updatedAt: number;
}

export interface SettingRecord {
  key: string;
  value: unknown;
}

export type Database = Dexie & {
  samples: EntityTable<SampleRecord, 'id'>;
  projects: EntityTable<ProjectRecord, 'id'>;
  settings: EntityTable<SettingRecord, 'key'>;
  kits: EntityTable<KitRecord, 'id'>;
};

export const db = new Dexie('sosample') as Database;

db.version(1).stores({
  samples: 'id, folder, name, updatedAt',
  projects: 'id, name, updatedAt',
  settings: 'key',
});

db.version(2).stores({
  samples: 'id, folder, name, updatedAt',
  projects: 'id, name, updatedAt',
  settings: 'key',
  kits: 'id, name, updatedAt',
});

export function newId(): string {
  return crypto.randomUUID();
}
