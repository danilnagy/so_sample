import { store, useAppFields } from '../store';

/** A notice (an import's outcome, an error) as a toast over the bottom bar; it goes after a few seconds or on a tap. */
export function Toast() {
  const { notice } = useAppFields('notice');
  if (!notice) return null;
  return (
    <div className="toast" role="status" aria-live="polite" title="Tap to dismiss" onClick={() => store.notify(null)}>
      {notice}
    </div>
  );
}
