import { createContext, useContext, useSyncExternalStore } from 'react';

/** Below this width the whole sequencer no longer fits, and the app shows its pad layout. */
export const NARROW_QUERY = '(max-width: 840px)';

const query = typeof window !== 'undefined' && 'matchMedia' in window ? window.matchMedia(NARROW_QUERY) : null;

/** Set by the guide around a phone-sized frame, so the components inside lay out as on a phone. */
export const NarrowOverride = createContext<boolean | null>(null);

/** Whether the viewport is too narrow for the sequencer (or the guide's frame says so); follows the window live. */
export function useNarrow(): boolean {
  const override = useContext(NarrowOverride);
  const narrow = useSyncExternalStore(
    (listen) => {
      query?.addEventListener('change', listen);
      return () => query?.removeEventListener('change', listen);
    },
    () => query?.matches ?? false,
    () => false,
  );
  return override ?? narrow;
}
