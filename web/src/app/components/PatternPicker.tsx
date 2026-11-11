import { useEffect, useRef } from 'react';

import { patternIsEmpty } from '../../core/pattern';
import { store, useAppFields } from '../store';

const SIZE = 4 * 28 + 3 * 3 + 2 * 4 + 2;

/**
 * The sixteen patterns as the device's 4x4 keys, floating above `anchor`: a click adds the
 * pattern to the end of the song and closes the picker, as do Escape and a click elsewhere.
 */
export function PatternPicker({ anchor, onClose }: { anchor: DOMRect; onClose: () => void }) {
  const { project } = useAppFields('project');
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const away = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) onClose();
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }
    };
    document.addEventListener('mousedown', away);
    document.addEventListener('keydown', key, true);
    return () => {
      document.removeEventListener('mousedown', away);
      document.removeEventListener('keydown', key, true);
    };
  }, [onClose]);
  if (!project) return null;
  // Above the chip when there is room, else below; kept inside the window sideways.
  const left = Math.max(4, Math.min(anchor.left, window.innerWidth - SIZE - 4));
  const style = anchor.top >= SIZE + 8 ? { left, bottom: window.innerHeight - anchor.top + 4 } : { left, top: anchor.bottom + 4 };
  return (
    <div ref={box} className="pattern-picker" role="dialog" aria-label="Add a pattern to the song" style={style}>
      {project.patterns.map((data, i) => (
        <button
          key={i}
          className={`pattern ${patternIsEmpty(data) ? '' : 'filled'}`}
          title={`Add pattern ${i + 1} to the end of the song`}
          onClick={() => {
            store.appendToChain(i + 1);
            onClose();
          }}
        >
          {i + 1}
        </button>
      ))}
    </div>
  );
}
