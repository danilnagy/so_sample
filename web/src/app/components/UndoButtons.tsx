import { store, useAppFields } from '../store';
import { RedoIcon, UndoIcon } from './Icons';

const MAC = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);
const KEY = MAC ? '⌘' : 'Ctrl+';

/** Undo and redo for the open project; in the top bar on a desktop, in the bottom bar on a phone. */
export function UndoButtons() {
  // Every edit, undo and redo replaces the project, so following it keeps the buttons current.
  useAppFields('project');
  return (
    <span className="undo-buttons">
      <button className="icon-button" disabled={!store.canUndo()} title={`Undo (${KEY}Z)`} aria-label="Undo" onClick={() => store.undo()}>
        <UndoIcon />
      </button>
      <button className="icon-button" disabled={!store.canRedo()} title={`Redo (${MAC ? '⇧⌘Z' : 'Ctrl+Y'})`} aria-label="Redo" onClick={() => store.redo()}>
        <RedoIcon />
      </button>
    </span>
  );
}
