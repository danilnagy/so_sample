/** Small inline icons, drawn in the current text colour. */

/** A small keyboard; `empty` draws it in the light stroke, like an unassigned drum key. */
export function KeysIcon({ empty = false }: { empty?: boolean }) {
  return (
    <svg className={`icon ${empty ? 'empty' : ''}`} width="16" height="14" viewBox="0 0 16 14" aria-hidden="true">
      <rect x="0.5" y="0.5" width="15" height="13" fill="none" stroke="currentColor" />
      <line x1="5.5" y1="0.5" x2="5.5" y2="13.5" stroke="currentColor" />
      <line x1="10.5" y1="0.5" x2="10.5" y2="13.5" stroke="currentColor" />
      <rect x="3.5" y="0.5" width="4" height="7.5" fill="currentColor" />
      <rect x="8.5" y="0.5" width="4" height="7.5" fill="currentColor" />
    </svg>
  );
}

/** The sixteen keys of a drum kit, filled where a slice is assigned. Display only. */
export function SlicesIcon({ filled }: { filled: boolean[] }) {
  return (
    <span className="icon slices" aria-hidden="true">
      {filled.map((on, k) => (
        <span key={k} className={on ? 'on' : ''} />
      ))}
    </span>
  );
}

export function PlayIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
      <path d="M2 1 L9 5 L2 9 Z" fill="currentColor" />
    </svg>
  );
}

/** Points down; flipped to point up when its section is open. */
export function ChevronIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
      <path d="M1.5 3.5 L5 7 L8.5 3.5" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

export function TrashIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M1.5 3 H10.5 M4.5 1.5 H7.5 M3 3 L3.7 10.5 H8.3 L9 3 M5 5 V9 M7 5 V9" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

export function PencilIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M1.5 10.5 L2 8.5 L8 2.5 L9.5 4 L3.5 10 Z M7 3.5 L8.5 5" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

/** The project is saved. */
export function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M2 6.5 L4.8 9.3 L10 3.5" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

/** A save is on its way. */
export function PendingIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

/** Export: an arrow down onto a line. */
export function DownloadIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M6 1.5 V8 M3 5.5 L6 8.5 L9 5.5 M1.5 10.5 H10.5" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

/** Duplicate: two overlapping sheets. */
export function CopyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M4.5 1.5 H10.5 V7.5 M1.5 4.5 H7.5 V10.5 H1.5 Z" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

/** The theme in force: a half-filled circle for System, a sun for Light, a moon for Dark. */
export function ThemeIcon({ theme }: { theme: 'system' | 'light' | 'dark' }) {
  if (theme === 'light') {
    return (
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <circle cx="7" cy="7" r="3" fill="none" stroke="currentColor" />
        <path d="M7 0.5v2M7 11.5v2M0.5 7h2M11.5 7h2M2.4 2.4l1.4 1.4M10.2 10.2l1.4 1.4M2.4 11.6l1.4-1.4M10.2 3.8l1.4-1.4" stroke="currentColor" strokeWidth="1" />
      </svg>
    );
  }
  if (theme === 'dark') {
    return (
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path d="M9.5 1.5a6 6 0 1 0 3 9.5 5 5 0 0 1-3-9.5z" fill="none" stroke="currentColor" />
      </svg>
    );
  }
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <circle cx="7" cy="7" r="5.5" fill="none" stroke="currentColor" />
      <path d="M7 1.5a5.5 5.5 0 0 1 0 11z" fill="currentColor" />
    </svg>
  );
}

/** Arrows for moving a song entry along the chain, and the handle that drags one. */
export function ArrowUpIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M6 10.5 V2 M2.5 5.5 L6 2 L9.5 5.5" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

export function ArrowDownIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M6 1.5 V10 M2.5 6.5 L6 10 L9.5 6.5" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

export function DragIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M2 3.5 H10 M2 6 H10 M2 8.5 H10" fill="none" stroke="currentColor" strokeWidth="1" />
    </svg>
  );
}

/** The transport's stop glyph for the narrowest screens, and the warning triangle. */
export function StopIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <rect x="2" y="2" width="8" height="8" fill="currentColor" />
    </svg>
  );
}

export function WarningIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M6 1.2 L11.2 10.5 H0.8 Z" fill="currentColor" />
      <path d="M6 4.2v3.2" stroke="var(--bg)" strokeWidth="1.3" />
      <circle cx="6" cy="9" r="0.75" fill="var(--bg)" />
    </svg>
  );
}

/** Undo and redo: a hooked arrow turning back, and its mirror. */
export function UndoIcon() {
  return (
    <svg width="14" height="12" viewBox="0 0 14 12" aria-hidden="true">
      <path d="M4.5 1.5 L1.5 4.5 L4.5 7.5 M1.5 4.5 H9 A3.5 3.5 0 0 1 9 11.5 H6" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

export function RedoIcon() {
  return (
    <svg width="14" height="12" viewBox="0 0 14 12" aria-hidden="true">
      <path d="M9.5 1.5 L12.5 4.5 L9.5 7.5 M12.5 4.5 H5 A3.5 3.5 0 0 0 5 11.5 H8" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}
