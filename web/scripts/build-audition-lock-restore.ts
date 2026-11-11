/**
 * Build the restore for the audition-lock observation with the app's own compiler.
 *
 *   npx tsx scripts/build-audition-lock-restore.ts <output folder>
 *
 * Sound 16 key 1 holds a 200 Hz sawtooth hit with 55 harmonics; Pattern 1 plays it on
 * steps 1, 5, 9 and 13 with the app's default locks on every note (pitch 13, volume 36,
 * filter 63, resonance 1), as every note the web app writes carries. Tempo 120, chain
 * of Pattern 1 alone. Writes restore.wav and hit.wav and prints their hashes.
 */

import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

import { encodeRestoreWav } from '../src/core/modem/encode';
import { labelsForBody } from '../src/core/labels';
import { SAMPLE_RATE, encodeMulaw } from '../src/core/mulaw';
import { encodePackets } from '../src/core/packets';
import { DEFAULT_PARAMETERS, emptyPattern, writeCell } from '../src/core/pattern';
import { type Project, compileProject } from '../src/core/project';
import { serializeState } from '../src/core/state';
import { emptyTemplateState } from '../src/core/template';
import { wavFromFloat } from '../src/core/wav';

export const HIT = { fundamentalHz: 200, harmonics: 55, seconds: 0.27, peak: 0.8 };
export const NOTE_STEPS = [1, 5, 9, 13];
export const SOUND = 16;
export const TEMPO = 120;

/** A band-limited sawtooth: harmonics at 1/h, scaled to the peak. */
function sawtooth(): Float64Array {
  const length = Math.round(HIT.seconds * SAMPLE_RATE);
  const out = new Float64Array(length);
  for (let i = 0; i < length; i++) {
    const t = i / SAMPLE_RATE;
    let v = 0;
    for (let h = 1; h <= HIT.harmonics; h++) v += Math.sin(2 * Math.PI * HIT.fundamentalHz * h * t) / h;
    out[i] = v;
  }
  let peak = 0;
  for (const v of out) peak = Math.max(peak, Math.abs(v));
  for (let i = 0; i < length; i++) out[i] = (out[i] / peak) * HIT.peak;
  return out;
}

function main(): void {
  const out = process.argv[2];
  if (!out) throw new Error('usage: build-audition-lock-restore.ts <output folder>');
  mkdirSync(out, { recursive: true });
  const samples = sawtooth();
  const codes = encodeMulaw(samples);
  const slices = new Array(16).fill(null);
  slices[0] = { sampleId: 'hit', start: 0, end: codes.length };
  const patterns = Array.from({ length: 16 }, () => emptyPattern());
  for (const step of NOTE_STEPS) writeCell(patterns[0], step, SOUND, { key: 1, ...DEFAULT_PARAMETERS });
  const drums = new Array(8).fill(null);
  drums[SOUND - 9] = { slices };
  const project: Project = { tempo: TEMPO, swing: 0, chain: [1], melodic: new Array(8).fill(null), drums, patterns };
  const state = compileProject(project, () => codes, emptyTemplateState());
  const restore = encodeRestoreWav(labelsForBody(encodePackets(serializeState(state))));
  const hit = wavFromFloat(samples, Math.round(SAMPLE_RATE));
  writeFileSync(join(out, 'restore.wav'), restore);
  writeFileSync(join(out, 'hit.wav'), hit);
  const sha = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex');
  console.log(
    JSON.stringify({
      restore_wav_sha256: sha(restore),
      hit_wav_sha256: sha(hit),
      hit_codes: codes.length,
      hit_codes_sha256: sha(codes),
      sound: SOUND,
      note_steps: NOTE_STEPS,
      locks: DEFAULT_PARAMETERS,
      tempo: TEMPO,
      restore_bytes: restore.length,
    }),
  );
}

main();
