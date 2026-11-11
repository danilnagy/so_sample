import { useEffect, useRef } from 'react';

interface Props {
  samples: Float64Array;
  /** Highlighted window, in samples. */
  start: number;
  end: number;
  /** Minimum window length, in samples. */
  minimum?: number;
  onChange?: (start: number, end: number) => void;
  height?: number;
  /** Where a preview is playing, in samples, drawn as a line. */
  playhead?: number | null;
  /** The edited result, drawn over the original from `offset`; the original then shows in the mid stroke behind it. */
  edited?: { samples: Float64Array; offset: number } | null;
}

interface Peaks {
  perPixel: number;
  offset: number;
  height: number;
  /** The first pixel column covered, then each column's top and height. */
  first: number;
  top: Float32Array;
  extent: Float32Array;
}

/** The peak column of each pixel `values` covers when placed at `offset` samples, clipped to full scale. */
function computePeaks(values: Float64Array, offset: number, perPixel: number, width: number, height: number): Peaks {
  const first = Math.max(0, Math.floor(offset / perPixel));
  const last = Math.min(width, Math.ceil((offset + values.length) / perPixel));
  const count = Math.max(0, last - first);
  const top = new Float32Array(count);
  const extent = new Float32Array(count);
  for (let x = first; x < last; x++) {
    const a = Math.max(0, Math.floor(x * perPixel) - offset);
    const b = Math.min(values.length, Math.floor((x + 1) * perPixel) + 1 - offset);
    let lo = 0;
    let hi = 0;
    for (let i = a; i < b; i++) {
      const v = Math.max(-1, Math.min(1, values[i]));
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    const y = (height / 2) * (1 - hi);
    top[x - first] = y;
    extent[x - first] = Math.max(1, (height / 2) * (1 - lo) - y);
  }
  return { perPixel, offset, height, first, top, extent };
}

/** A peak waveform with two draggable window handles and, while a preview plays, a playhead. */
export function Waveform({ samples, start, end, minimum = 128, onChange, height = 120, playhead = null, edited = null }: Props) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const drag = useRef<'start' | 'end' | null>(null);
  /** The latest draw, for the resize observer, which lives as long as the canvas. */
  const redraw = useRef<() => void>(() => {});
  /** Peak columns per data array, kept across playhead frames; recomputed when the width or placement changes. */
  const peaks = useRef(new WeakMap<Float64Array, Peaks>());

  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const observer = new ResizeObserver(() => redraw.current());
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const draw = () => {
      const width = element.clientWidth;
      element.width = width * devicePixelRatio;
      element.height = height * devicePixelRatio;
      const ctx = element.getContext('2d');
      if (!ctx) return;
      ctx.scale(devicePixelRatio, devicePixelRatio);
      const styles = getComputedStyle(element);
      const fg = styles.getPropertyValue('--fg').trim();
      const mid = styles.getPropertyValue('--stroke-mid').trim();
      const line = styles.getPropertyValue('--stroke').trim();
      const strong = styles.getPropertyValue('--stroke-strong').trim();
      const soft = styles.getPropertyValue('--soft').trim();
      ctx.clearRect(0, 0, width, height);
      const x0 = (start / samples.length) * width;
      const x1 = (end / samples.length) * width;
      ctx.fillStyle = soft;
      ctx.fillRect(x0, 0, x1 - x0, height);
      ctx.strokeStyle = line;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
      const perPixel = samples.length / width;
      /** Draw an envelope: `values` placed at `offset` samples, between pixel columns covering it, clipped to full scale. */
      const envelope = (values: Float64Array, offset: number, color: string) => {
        let cached = peaks.current.get(values);
        if (!cached || cached.perPixel !== perPixel || cached.offset !== offset || cached.height !== height) {
          cached = computePeaks(values, offset, perPixel, width, height);
          peaks.current.set(values, cached);
        }
        ctx.fillStyle = color;
        for (let i = 0; i < cached.top.length; i++) ctx.fillRect(cached.first + i, cached.top[i], 1, cached.extent[i]);
      };
      envelope(samples, 0, edited ? mid : fg);
      if (edited) envelope(edited.samples, edited.offset, fg);
      ctx.fillStyle = fg;
      ctx.fillRect(x0 - 1, 0, 2, height);
      ctx.fillRect(x1 - 1, 0, 2, height);
      if (playhead !== null) {
        ctx.fillStyle = strong;
        ctx.fillRect(Math.round((playhead / samples.length) * width), 0, 1, height);
      }
    };
    redraw.current = draw;
    draw();
  }, [samples, start, end, height, playhead, edited]);

  const position = (e: React.PointerEvent): number => {
    const rect = canvas.current!.getBoundingClientRect();
    return Math.round(((e.clientX - rect.left) / rect.width) * samples.length);
  };

  return (
    <canvas
      ref={canvas}
      className="waveform"
      style={{ height, cursor: onChange ? 'col-resize' : 'default' }}
      onPointerDown={(e) => {
        if (!onChange) return;
        const p = position(e);
        drag.current = Math.abs(p - start) <= Math.abs(p - end) ? 'start' : 'end';
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
        move(p);
      }}
      onPointerMove={(e) => drag.current && move(position(e))}
      onPointerUp={() => (drag.current = null)}
    />
  );

  function move(p: number): void {
    if (!onChange) return;
    const clamp = (v: number) => Math.max(0, Math.min(samples.length, v));
    if (drag.current === 'start') onChange(Math.max(0, Math.min(clamp(p), end - minimum)), end);
    else onChange(start, Math.min(samples.length, Math.max(clamp(p), start + minimum)));
  }
}
