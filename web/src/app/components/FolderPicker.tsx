import { useEffect, useRef, useState } from 'react';

const WIDTH = 240;
const MAX_HEIGHT = 240;

/**
 * A combobox for a sample's folder: type to search the existing folders, pick one, pick
 * no folder, or create the typed name. It floats over everything, fixed to the viewport
 * under (or, near the bottom, above) the `anchor` rectangle, and closes on pick, Escape,
 * a click elsewhere, or when the page scrolls.
 */
export function FolderPicker({ value, folders, anchor, onPick, onClose }: { value: string; folders: string[]; anchor: DOMRect; onPick: (folder: string) => void; onClose: () => void }) {
  const [text, setText] = useState('');
  const [active, setActive] = useState(0);
  const box = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    input.current?.focus();
    const away = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) onClose();
    };
    const scrolled = (e: Event) => {
      if (box.current && !box.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', away);
    document.addEventListener('scroll', scrolled, true);
    window.addEventListener('resize', onClose);
    return () => {
      document.removeEventListener('mousedown', away);
      document.removeEventListener('scroll', scrolled, true);
      window.removeEventListener('resize', onClose);
    };
  }, [onClose]);
  const below = anchor.bottom + MAX_HEIGHT <= window.innerHeight || anchor.top < MAX_HEIGHT;
  const left = Math.max(4, Math.min(anchor.left, window.innerWidth - WIDTH - 4));
  const style = below ? { left, top: anchor.bottom } : { left, bottom: window.innerHeight - anchor.top };
  const query = text.trim();
  const matches = folders.filter((f) => f && f.toLowerCase().includes(query.toLowerCase()));
  const canCreate = query !== '' && !folders.some((f) => f.toLowerCase() === query.toLowerCase());
  /** The choices in order: matching folders, then no folder, then the new name. */
  const choices: { label: string; folder: string; kind: 'folder' | 'none' | 'new' }[] = [
    ...matches.map((f) => ({ label: f, folder: f, kind: 'folder' as const })),
    ...(query === '' || '(no folder)'.includes(query.toLowerCase()) ? [{ label: '(no folder)', folder: '', kind: 'none' as const }] : []),
    ...(canCreate ? [{ label: `Create "${query}"`, folder: query, kind: 'new' as const }] : []),
  ];
  const current = Math.min(active, Math.max(0, choices.length - 1));
  return (
    <div
      ref={box}
      className="folder-picker"
      style={style}
      role="dialog"
      aria-label="Choose a folder"
      onKeyDown={(e) => {
        // Handled here so the modal's own Escape stays out of it.
        e.stopPropagation();
        if (e.key === 'Escape') onClose();
        else if (e.key === 'ArrowDown') setActive(Math.min(choices.length - 1, current + 1));
        else if (e.key === 'ArrowUp') setActive(Math.max(0, current - 1));
        else if (e.key === 'Enter' && choices[current]) onPick(choices[current].folder);
      }}
    >
      <input
        ref={input}
        value={text}
        placeholder="Search or type a new folder"
        aria-label="Folder"
        onChange={(e) => {
          setText(e.target.value);
          setActive(0);
        }}
      />
      <div className="choices" role="listbox">
        {choices.map((c, i) => (
          <button
            key={`${c.kind}:${c.folder}`}
            role="option"
            aria-selected={i === current}
            className={`${i === current ? 'active' : ''} ${c.folder === value ? 'current' : ''}`}
            onMouseEnter={() => setActive(i)}
            onClick={() => onPick(c.folder)}
          >
            {c.label}
            {c.folder === value && c.kind !== 'new' ? ' ✓' : ''}
          </button>
        ))}
        {choices.length === 0 && <p className="muted">No folder matches.</p>}
      </div>
    </div>
  );
}
