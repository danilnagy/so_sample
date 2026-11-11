import { useEffect, useRef, useState } from 'react';

import { WarningIcon } from './Icons';

/**
 * A warning glyph with its explanation: the tooltip on hover, and a popover on a tap, since
 * touch has no hover. It sits inside pattern buttons, step cells and pads, and takes the
 * tap itself so the element under it keeps its own behaviour.
 */
export function WarnGlyph({ text, className = '' }: { text: string; className?: string }) {
  const [anchor, setAnchor] = useState<DOMRect | null>(null);
  return (
    <>
      <span
        className={`warn-glyph ${className}`}
        role="button"
        tabIndex={0}
        aria-label={text}
        title={text}
        onClick={(e) => {
          e.stopPropagation();
          setAnchor(anchor ? null : e.currentTarget.getBoundingClientRect());
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            e.stopPropagation();
            setAnchor(anchor ? null : e.currentTarget.getBoundingClientRect());
          }
        }}
      >
        <WarningIcon />
      </span>
      {anchor && <HintPopover anchor={anchor} text={text} onClose={() => setAnchor(null)} />}
    </>
  );
}

function HintPopover({ anchor, text, onClose }: { anchor: DOMRect; text: string; onClose: () => void }) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const away = (e: PointerEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) onClose();
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }
    };
    document.addEventListener('pointerdown', away, true);
    document.addEventListener('keydown', key, true);
    return () => {
      document.removeEventListener('pointerdown', away, true);
      document.removeEventListener('keydown', key, true);
    };
  }, [onClose]);
  const width = Math.min(280, window.innerWidth - 16);
  const left = Math.max(8, Math.min(anchor.left, window.innerWidth - width - 8));
  // Above the glyph when there is room, else below.
  const style = anchor.top > 120 ? { left, width, bottom: window.innerHeight - anchor.top + 6 } : { left, width, top: anchor.bottom + 6 };
  return (
    <div ref={box} className="hint-popover" role="tooltip" style={style}>
      {text}
    </div>
  );
}
