import { useMemo } from 'react';

import { MULAW_LEVELS } from '../../core/mulaw';
import { ROW_HEIGHT } from '../tokens';

/**
 * A sample's shape in a row: the envelope of its codes, one column per pixel, with the
 * windows that play from it marked behind. Always one row tall, wherever it appears.
 */
const height = ROW_HEIGHT;

/** Envelope paths by sample codes and width, shared by every row that shows the same sample. */
const cache = new WeakMap<Uint8Array, Map<number, string>>();

function envelopePath(codes: Uint8Array, columns: number): string {
  let byWidth = cache.get(codes);
  if (!byWidth) cache.set(codes, (byWidth = new Map()));
  const cached = byWidth.get(columns);
  if (cached !== undefined) return cached;
  const n = codes.length;
  let path = '';
  if (n) {
    const used = Math.min(columns, n);
    const top: string[] = [];
    const bottom: string[] = [];
    const mid = height / 2;
    for (let c = 0; c < used; c++) {
      const from = Math.floor((c * n) / used);
      const to = Math.max(from + 1, Math.floor(((c + 1) * n) / used));
      let max = 0;
      let min = 0;
      for (let i = from; i < to; i++) {
        const v = MULAW_LEVELS[codes[i]];
        if (v > max) max = v;
        if (v < min) min = v;
      }
      const x = ((c + 0.5) * columns) / used;
      top.push(`${x.toFixed(1)},${(mid - Math.max(max * mid, 0.5)).toFixed(1)}`);
      bottom.push(`${x.toFixed(1)},${(mid - Math.min(min * mid, -0.5)).toFixed(1)}`);
    }
    path = `M${top.join(' L')} L${bottom.reverse().join(' L')} Z`;
  }
  byWidth.set(columns, path);
  return path;
}

export function MiniWave({ codes, windows, title, width = 160 }: { codes: Uint8Array; windows: { start: number; end: number }[]; title?: string; width?: number }) {
  const COLUMNS = width;
  const path = useMemo(() => envelopePath(codes, COLUMNS), [codes, COLUMNS]);
  const scale = codes.length ? COLUMNS / codes.length : 0;
  return (
    <svg className="miniwave" width={COLUMNS} height={height} viewBox={`0 0 ${COLUMNS} ${height}`} aria-hidden={title ? undefined : true} role={title ? 'img' : undefined}>
      {title && <title>{title}</title>}
      {windows.map((w, i) => (
        <rect key={i} className="window" x={w.start * scale} y={0} width={Math.max(1, (w.end - w.start) * scale)} height={height} />
      ))}
      <path className="wave" d={path} />
    </svg>
  );
}
