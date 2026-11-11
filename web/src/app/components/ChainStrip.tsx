import { memo, useEffect, useRef, useState } from 'react';

import { store, useAppFields } from '../store';
import { usePlaybackPick } from '../usePlayhead';
import { PatternPicker } from './PatternPicker';

function ChainStripView() {
  const { project, songEntry } = useAppFields('project', 'songEntry');
  const [dragging, setDragging] = useState<number | null>(null);
  /** The add chip's rectangle while its picker is open. */
  const [adding, setAdding] = useState<DOMRect | null>(null);
  const playingEntry = usePlaybackPick((p) => p?.entry ?? null);
  const strip = useRef<HTMLDivElement>(null);
  /** The visible part of the chips as fractions of the whole, or null when they all fit. */
  const [thumb, setThumb] = useState<{ left: number; width: number } | null>(null);
  const chainLength = project?.chain.length ?? 0;
  useEffect(() => {
    const element = strip.current;
    if (!element) return;
    const measure = () => {
      const { scrollLeft, scrollWidth, clientWidth } = element;
      setThumb(scrollWidth > clientWidth + 1 ? { left: scrollLeft / scrollWidth, width: clientWidth / scrollWidth } : null);
    };
    measure();
    element.addEventListener('scroll', measure);
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => {
      element.removeEventListener('scroll', measure);
      observer.disconnect();
    };
  }, [chainLength]);
  if (!project) return null;
  const chain = project.chain;
  /** A press on the bar scrolls the chips so the thumb follows the pointer. */
  const scrollTo = (e: React.PointerEvent<HTMLDivElement>) => {
    const element = strip.current;
    if (!element) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const fraction = (e.clientX - rect.left) / rect.width - (thumb?.width ?? 0) / 2;
    element.scrollLeft = Math.max(0, Math.min(1, fraction)) * element.scrollWidth;
  };
  const move = (from: number, to: number) => {
    if (from === to) return;
    const next = chain.slice();
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    store.setChain(next);
  };
  return (
    <div className="chain">
      <span className="muted" style={{ width: 200, flex: 'none' }}>
        Song
      </span>
      {/* The chips scroll on their own when the song is long, with a bar of their own under them; the count stays put at the right. */}
      <div className="chips-wrap">
        <div className="chips" id="song-chips" ref={strip}>
        {/* A click selects an entry for the move and remove buttons at the right; chips also drag to reorder. */}
        {chain.map((pattern, i) => (
        <span
          key={i}
          role="button"
          tabIndex={0}
          aria-pressed={songEntry === i}
          className={`chip ${songEntry === i ? 'on' : ''} ${playingEntry === i ? 'playing' : ''}`}
          draggable
          title={`Entry ${i + 1}: pattern ${pattern}.${i === 0 ? ' The first pattern is what the device plays after a restore.' : ''} Click to select; drag to reorder.`}
          onClick={() => store.selectSongEntry(i)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              store.selectSongEntry(i);
            }
          }}
          onDragStart={() => setDragging(i)}
          onDragOver={(e) => e.preventDefault()}
          onDrop={() => {
            if (dragging !== null) move(dragging, i);
            setDragging(null);
          }}
        >
          {pattern}
        </span>
        ))}
          <button
            className={`chip add ${adding ? 'on' : ''}`}
            title={chain.length >= 128 ? 'The song holds 128 patterns' : 'Add a pattern to the end of the song'}
            aria-label="Add a pattern to the song"
            disabled={chain.length >= 128}
            onClick={(e) => setAdding(adding ? null : e.currentTarget.getBoundingClientRect())}
          >
            +
          </button>
          {adding && <PatternPicker anchor={adding} onClose={() => setAdding(null)} />}
        </div>
        {thumb && (
          <div
            className="scrollbar"
            role="scrollbar"
            aria-controls="song-chips"
            aria-valuenow={Math.round(thumb.left * 100)}
            onPointerDown={(e) => {
              e.currentTarget.setPointerCapture(e.pointerId);
              scrollTo(e);
            }}
            onPointerMove={(e) => e.buttons && scrollTo(e)}
          >
            <div className="thumb" style={{ left: `${thumb.left * 100}%`, width: `${thumb.width * 100}%` }} />
          </div>
        )}
      </div>
      {songEntry !== null && (
        <span className="entry-actions">
          <button disabled={songEntry === 0} title="Move the selected entry one place earlier" onClick={() => store.moveSongEntry(-1)}>
            Move left
          </button>
          <button disabled={songEntry >= chain.length - 1} title="Move the selected entry one place later" onClick={() => store.moveSongEntry(1)}>
            Move right
          </button>
          <button disabled={chain.length === 1} title={chain.length === 1 ? 'The song keeps at least one pattern' : 'Remove the selected entry from the song'} onClick={() => store.removeSongEntry()}>
            Remove
          </button>
        </span>
      )}
      <button onClick={() => confirm('Clear the song? Pattern 1 alone stays.') && store.clearChain()}>Clear</button>
      <span className="count" title="Patterns in the song, of the 128 the device holds. Shift-click a pattern above to add it; click a chip to move or remove it; drag chips to reorder.">
        {chain.length} / 128
      </span>
    </div>
  );
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const ChainStrip = memo(ChainStripView);
