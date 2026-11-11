import { useCallback, useEffect, useRef, useState } from 'react';

import type { PlaybackPosition } from './player';
import type { Playback } from './samples';
import { store, useAppFields } from './store';

/**
 * The position of a preview as it plays, for a playhead: `play` starts a playback and the
 * position is followed frame by frame until it ends.
 */
export function usePlayhead(): [number | null, (start: () => Playback) => void] {
  const [playhead, setPlayhead] = useState<number | null>(null);
  const frame = useRef(0);
  useEffect(() => () => cancelAnimationFrame(frame.current), []);
  const play = useCallback((start: () => Playback) => {
    cancelAnimationFrame(frame.current);
    const playback = start();
    const tick = () => {
      const position = playback.position();
      setPlayhead(position);
      if (position !== null) frame.current = requestAnimationFrame(tick);
    };
    tick();
  }, []);
  return [playhead, play];
}

/**
 * The key each sound is sounding (by sound index, null when silent), followed frame by
 * frame while the preview plays or an audition sounds; the polling stops when both are quiet.
 */
export function useSoundingKeys(): (number | null)[] {
  const { playing, auditionTick } = useAppFields('playing', 'auditionTick');
  const [keys, setKeys] = useState<(number | null)[]>(() => new Array(16).fill(null));
  useEffect(() => {
    const silence = new Array<number | null>(16).fill(null);
    const quiet = () => setKeys((k) => (k.some((key) => key !== null) ? silence : k));
    if (!playing && !store.auditioning()) {
      quiet();
      return;
    }
    let frame = 0;
    let last = '';
    const tick = () => {
      const next = store.soundingKeys();
      const signature = next.join(',');
      if (signature !== last) {
        last = signature;
        setKeys(next);
      }
      // Polling ends with the sound; the last reading is cleared so nothing stays lit.
      if (store.state.playing || store.auditioning()) frame = requestAnimationFrame(tick);
      else quiet();
    };
    tick();
    return () => cancelAnimationFrame(frame);
  }, [playing, auditionTick]);
  return keys;
}

/**
 * One value derived from where the preview is (the pattern playing, the song entry, the
 * step of a given pattern), followed frame by frame while it plays: the component
 * re-renders only when that value changes, not on every step. `pick` should return a
 * primitive; it gets null when stopped.
 */
export function usePlaybackPick<T>(pick: (position: PlaybackPosition | null) => T): T {
  const { playing } = useAppFields('playing');
  const pickRef = useRef(pick);
  useEffect(() => {
    pickRef.current = pick;
  });
  const [value, setValue] = useState<T>(() => pick(null));
  useEffect(() => {
    if (!playing) {
      setValue(pickRef.current(null));
      return;
    }
    let frame = 0;
    const tick = () => {
      const next = pickRef.current(store.playbackPosition());
      setValue((previous) => (Object.is(previous, next) ? previous : next));
      frame = requestAnimationFrame(tick);
    };
    tick();
    return () => cancelAnimationFrame(frame);
  }, [playing]);
  return playing ? value : pick(null);
}
