import { useEffect, useRef, useState } from 'react';

import { MEMORY_PAGES } from '../../core/project';
import { store, useAppFields } from '../store';
import { useNarrow } from '../useNarrow';
import { PlayIcon, StopIcon, WarningIcon } from './Icons';
import { UndoButtons } from './UndoButtons';

/**
 * The bottom bar, one row at every width: the transport at the left (words, or glyphs on
 * the narrowest screens), tempo and swing beside it (two fields, or on a phone one button
 * that opens steppers), and the memory meter at the right, which turns to the warning
 * style when the project outgrows the device. Notices show as a toast over the bar, and
 * the four-voice warning on the patterns and steps concerned.
 */
export function StatusBar() {
  // The samples too: the memory meter counts them, and a trim or resample changes it without touching the project.
  const { project, playing, playbackMode, followPlayhead } = useAppFields('project', 'samples', 'playing', 'playbackMode', 'followPlayhead');
  const narrow = useNarrow();
  if (!project) return null;
  const pages = store.pages();
  const over = pages !== null && pages > MEMORY_PAGES;
  return (
    <div className="statusbar">
      <span className="transport-group">
        <button className={`transport ${playing ? 'on' : ''}`} title="Play or stop the preview (Space)" aria-label={playing ? 'Stop' : 'Play'} onClick={() => store.togglePlayback()}>
          <span className="word">{playing ? 'Stop' : 'Play'}</span>
          <span className="glyph">{playing ? <StopIcon /> : <PlayIcon />}</span>
        </button>
        <span className="mode" role="radiogroup" aria-label="Playback mode">
          <button className={playbackMode === 'pattern' ? 'on' : ''} role="radio" aria-checked={playbackMode === 'pattern'} aria-label="Pattern" title="Loop the selected pattern" onClick={() => store.setPlaybackMode('pattern')}>
            <span className="word">Pattern</span>
            <span className="glyph">P</span>
          </button>
          <button className={playbackMode === 'song' ? 'on' : ''} role="radio" aria-checked={playbackMode === 'song'} aria-label="Song" title="Play the song chain" onClick={() => store.setPlaybackMode('song')}>
            <span className="word">Song</span>
            <span className="glyph">S</span>
          </button>
        </span>
        {/* Following only means something in song mode; the button stays in place, disabled, in pattern mode. */}
        <button
          className={followPlayhead && playbackMode === 'song' ? 'on' : ''}
          disabled={playbackMode !== 'song'}
          aria-pressed={followPlayhead}
          aria-label="Follow"
          title={playbackMode === 'song' ? 'Show the pattern that is sounding' : 'Follow the song: in song mode, the pattern on screen changes with the song'}
          onClick={() => void store.setFollowPlayhead(!followPlayhead)}
        >
          <span className="word">Follow</span>
          <span className="glyph">F</span>
        </button>
        {narrow ? (
          <TempoButton tempo={project.tempo} swing={project.swing} />
        ) : (
          <span className="tempo">
            <label title="Tempo, 60 to 240 BPM">
              Tempo
              <input type="number" min={60} max={240} value={project.tempo} aria-label="Tempo" onChange={(e) => store.setTempo(Number(e.target.value))} />
            </label>
            <label title="Swing, 0 to 18: even steps are delayed by this many 24ths of a step">
              Swing
              <input type="number" min={0} max={18} value={project.swing} aria-label="Swing" onChange={(e) => store.setSwing(Number(e.target.value))} />
            </label>
          </span>
        )}
      </span>
      <div className="spacer" />
      {/* On a phone, undo and redo live here, beside the memory meter; the top bar has no room. */}
      {narrow && <UndoButtons />}
      <button
        className={`memory ${over ? 'over' : ''}`}
        aria-label={pages === null ? 'Memory: cannot be compiled' : `Memory: ${pages} of ${MEMORY_PAGES} pages`}
        title={
          pages === null
            ? 'The project cannot be compiled; click for the reason'
            : over
              ? `Over the device's memory: ${pages} of ${MEMORY_PAGES} pages. Click for the breakdown.`
              : `Sample memory: ${pages} of ${MEMORY_PAGES} pages the device holds. Click for the breakdown.`
        }
        onClick={() => store.openMemory()}
      >
        {over && (
          <span className="glyph-inline" aria-label="Over the device's memory">
            <WarningIcon />
          </span>
        )}
        <span className="meter" aria-hidden="true">
          <span style={{ width: `${Math.min(100, ((pages ?? 0) / MEMORY_PAGES) * 100)}%` }} />
        </span>
        <span className="count">
          <span className="label-text">memory </span>
          {pages === null ? '–' : `${pages} / ${MEMORY_PAGES}`}
          <span className="label-text"> pages</span>
        </span>
      </button>
    </div>
  );
}

/** On a phone, tempo and swing as one button that opens a popover with steppers. */
function TempoButton({ tempo, swing }: { tempo: number; swing: number }) {
  const [anchor, setAnchor] = useState<DOMRect | null>(null);
  return (
    <>
      <button className="tempo-button" title={`Tempo ${tempo} BPM, swing ${swing}`} aria-label={`Tempo ${tempo} BPM, swing ${swing}`} aria-haspopup="dialog" aria-expanded={!!anchor} onClick={(e) => setAnchor(anchor ? null : e.currentTarget.getBoundingClientRect())}>
        {/* The words go on the smallest screens, leaving tempo / swing. */}
        <span className="long">
          {tempo} bpm · sw {swing}
        </span>
        <span className="short">
          {tempo} / {swing}
        </span>
      </button>
      {anchor && <TempoPopover anchor={anchor} tempo={tempo} swing={swing} onClose={() => setAnchor(null)} />}
    </>
  );
}

function TempoPopover({ anchor, tempo, swing, onClose }: { anchor: DOMRect; tempo: number; swing: number; onClose: () => void }) {
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
  const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
  // The popover is the button grown upwards and leftwards: its bottom-right corner sits on the button's.
  const style = { right: Math.max(4, window.innerWidth - anchor.right), bottom: Math.max(4, window.innerHeight - anchor.bottom) };
  return (
    <div ref={box} className="tempo-popover" role="dialog" aria-label="Tempo and swing" style={style}>
      <span>Tempo</span>
      <button aria-label="Slower" onClick={() => store.setTempo(clamp(tempo - 1, 60, 240))}>
        −
      </button>
      <span className="value">{tempo}</span>
      <button aria-label="Faster" onClick={() => store.setTempo(clamp(tempo + 1, 60, 240))}>
        +
      </button>
      <span>Swing</span>
      <button aria-label="Less swing" onClick={() => store.setSwing(clamp(swing - 1, 0, 18))}>
        −
      </button>
      <span className="value">{swing}</span>
      <button aria-label="More swing" onClick={() => store.setSwing(clamp(swing + 1, 0, 18))}>
        +
      </button>
    </div>
  );
}
