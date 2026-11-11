/**
 * Decode a backup recording with the web app's decoder and compare it to a restore.
 *
 *   npx tsx scripts/check-backup.ts <backup.wav> <restore.wav>
 *
 * Prints one JSON line: whether the backup decoded, by which method, whether its
 * packets and parsed state equal the restore's, and when they do not, every byte that
 * differs: global record bytes, pattern cells and footers, and sound records. The
 * app's decoder searches for the preamble past noise, which the Python harness decoder
 * does not.
 */

import { readFileSync } from 'node:fs';

import { recoverFrame } from '../src/core/modem/decode';
import { packetsEqual } from '../src/core/packets';
import { cellOffsets } from '../src/core/pattern';
import { type DeviceState, parseFrame, statesEqual } from '../src/core/state';
import { parseWav } from '../src/core/wav';

interface Change {
  region: 'global' | 'pattern' | 'sound';
  where: Record<string, number | string>;
  old?: number | string;
  new?: number | string;
}

/** Where a pattern byte lives: a cell's primary or auxiliary byte, or the effects footer. */
function patternPlace(offset: number): Record<string, number | string> {
  for (let step = 1; step <= 16; step++) {
    for (let sound = 1; sound <= 16; sound++) {
      const { primary, aux } = cellOffsets(step, sound);
      if (offset >= primary && offset < primary + 3) return { step, sound, part: 'primary', byte: offset - primary };
      if (offset === aux) return { step, sound, part: 'auxiliary' };
    }
  }
  return { part: 'footer', byte: offset - 1024 };
}

function differences(a: DeviceState, b: DeviceState): Change[] {
  const out: Change[] = [];
  a.globals.forEach((g, record) => {
    for (let i = 0; i < g.length; i++) if (g[i] !== b.globals[record][i]) out.push({ region: 'global', where: { record, offset: i }, old: g[i], new: b.globals[record][i] });
  });
  a.patterns.forEach((p, index) => {
    for (let i = 0; i < p.length; i++) if (p[i] !== b.patterns[index][i]) out.push({ region: 'pattern', where: { pattern: index + 1, offset: i, ...patternPlace(i) }, old: p[i], new: b.patterns[index][i] });
  });
  a.sounds.forEach((s, id) => {
    const t = b.sounds[id];
    if (!s && !t) return;
    if (!s || !t) {
      out.push({ region: 'sound', where: { id }, old: s ? 'record' : 'none', new: t ? 'record' : 'none' });
      return;
    }
    for (const field of ['start', 'end', 'owner'] as const) if (s[field] !== t[field]) out.push({ region: 'sound', where: { id, field }, old: s[field], new: t[field] });
    if (s.codes.length !== t.codes.length) out.push({ region: 'sound', where: { id, field: 'codes' }, old: s.codes.length, new: t.codes.length });
    else {
      let differing = 0;
      for (let i = 0; i < s.codes.length; i++) if (s.codes[i] !== t.codes[i]) differing++;
      if (differing) out.push({ region: 'sound', where: { id, field: 'codes' }, old: `${differing} codes differ`, new: `${differing} codes differ` });
    }
  });
  return out;
}

function main(): void {
  const [backup, restore] = process.argv.slice(2);
  if (!backup || !restore) throw new Error('usage: check-backup.ts <backup.wav> <restore.wav>');
  const target = recoverFrame(parseWav(new Uint8Array(readFileSync(restore)))).frame;
  const wav = parseWav(new Uint8Array(readFileSync(backup)));
  const peak = Math.max(...wav.channels.map((c) => c.reduce((m, v) => Math.max(m, Math.abs(v)), 0)));
  try {
    const { frame, attempts } = recoverFrame(wav);
    const actual = parseFrame(frame);
    const expected = parseFrame(target);
    const equal = statesEqual(actual, expected);
    console.log(
      JSON.stringify({
        decoded: true,
        method: attempts[attempts.length - 1].method,
        packets: frame.packets.length,
        peak,
        exact_target: packetsEqual(frame.packets, target.packets),
        state_equal: equal,
        changes: equal ? [] : differences(expected, actual),
      }),
    );
  } catch (error) {
    console.log(JSON.stringify({ decoded: false, peak, error: (error as Error).message }));
  }
}

main();
